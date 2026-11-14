import asyncio
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_seed():
    from app.db.session import AsyncSessionLocal
    from app.services.career_seeder import CareerSeeder
    from app.services.skill_seeder import SkillSeeder

    logger.info("Connecting to database and seeding...")
    async with AsyncSessionLocal() as session:
        await SkillSeeder.seed_canonical_skills(session)
        logger.info("Skills seeded.")
        await CareerSeeder.seed_career_data(session)
        logger.info("Careers and resources seeded successfully.")

if __name__ == "__main__":
    asyncio.run(run_seed())
