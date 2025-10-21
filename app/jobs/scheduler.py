"""Scheduler for One Market platform.

This module provides the main scheduler for running periodic jobs
with tolerance to missing data.
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
import traceback

from app.jobs.daily_rank import DailyRankJob
from app.jobs.make_recommendation import MakeRecommendationJob
from app.jobs.publish_briefing import PublishBriefingJob
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OneMarketScheduler:
    """Main scheduler for One Market platform."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.jobs = {
            'daily_rank': DailyRankJob(),
            'make_recommendation': MakeRecommendationJob(),
            'publish_briefing': PublishBriefingJob()
        }
        self.running = False
        
        logger.info("OneMarketScheduler initialized")
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        logger.info("Starting One Market Scheduler")
        
        try:
            # Schedule jobs
            await self._schedule_jobs()
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            self.running = False
            raise
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
        logger.info("One Market Scheduler stopped")
    
    async def _schedule_jobs(self):
        """Schedule all jobs."""
        # Daily rank job - runs at 6:00 AM UTC
        asyncio.create_task(self._run_periodic_job(
            'daily_rank',
            hour=6,
            minute=0,
            description="Daily strategy ranking"
        ))
        
        # Make recommendation job - runs at 7:00 AM UTC
        asyncio.create_task(self._run_periodic_job(
            'make_recommendation',
            hour=7,
            minute=0,
            description="Daily recommendation generation"
        ))
        
        # Publish briefing job - runs at 8:00 AM UTC
        asyncio.create_task(self._run_periodic_job(
            'publish_briefing',
            hour=8,
            minute=0,
            description="Daily briefing publication"
        ))
        
        logger.info("All jobs scheduled")
    
    async def _run_periodic_job(self, job_name: str, hour: int, minute: int, description: str):
        """Run a job periodically at specified time."""
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If time has passed today, schedule for tomorrow
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                # Wait until next run time
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Next {job_name} run in {wait_seconds/3600:.1f} hours")
                
                await asyncio.sleep(wait_seconds)
                
                if not self.running:
                    break
                
                # Run the job
                logger.info(f"Running {job_name}: {description}")
                await self._run_job(job_name)
                
            except Exception as e:
                logger.error(f"Error in {job_name} scheduler: {e}")
                logger.error(traceback.format_exc())
                # Wait 1 hour before retrying
                await asyncio.sleep(3600)
    
    async def _run_job(self, job_name: str):
        """Run a specific job."""
        try:
            job = self.jobs.get(job_name)
            if not job:
                logger.error(f"Job {job_name} not found")
                return
            
            # Run job with timeout
            await asyncio.wait_for(job.run(), timeout=3600)  # 1 hour timeout
            
            logger.info(f"Job {job_name} completed successfully")
            
        except asyncio.TimeoutError:
            logger.error(f"Job {job_name} timed out after 1 hour")
        except Exception as e:
            logger.error(f"Job {job_name} failed: {e}")
            logger.error(traceback.format_exc())
    
    async def run_job_now(self, job_name: str) -> Dict[str, Any]:
        """Run a job immediately (for testing/manual execution).
        
        Args:
            job_name: Name of job to run
            
        Returns:
            Job execution result
        """
        try:
            job = self.jobs.get(job_name)
            if not job:
                return {"success": False, "error": f"Job {job_name} not found"}
            
            logger.info(f"Running {job_name} manually")
            result = await job.run()
            
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"Manual job {job_name} failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all jobs.
        
        Returns:
            Dictionary with job statuses
        """
        status = {
            "scheduler_running": self.running,
            "jobs": {}
        }
        
        for job_name, job in self.jobs.items():
            status["jobs"][job_name] = {
                "name": job_name,
                "last_run": getattr(job, 'last_run', None),
                "last_success": getattr(job, 'last_success', None),
                "last_error": getattr(job, 'last_error', None)
            }
        
        return status


# Global scheduler instance
scheduler = OneMarketScheduler()


async def start_scheduler():
    """Start the global scheduler."""
    await scheduler.start()


async def stop_scheduler():
    """Stop the global scheduler."""
    await scheduler.stop()


async def run_job_manual(job_name: str) -> Dict[str, Any]:
    """Run a job manually."""
    return await scheduler.run_job_now(job_name)


def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status."""
    return scheduler.get_job_status()
