"""
Seed script: adds blocks, bins, cleaner assignments and tasks for testing.
Safe to run on top of init_db.py output (skips existing blocks/bins).

Usage:
    docker exec -w /app -e PYTHONPATH=/app waste_backend python3 scripts/seed_test_data.py
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select
from core.database import AsyncSessionLocal as Session
from models.user import User
from models.block import Block
from models.bin import Bin
from models.task import Task
from models.cleaner_block import CleanerBlock


async def get_or_create_block(db, name, floors, bpf):
    r = await db.execute(select(Block).where(Block.name == name))
    b = r.scalars().first()
    if not b:
        b = Block(name=name, total_floors=floors, bins_per_floor=bpf)
        db.add(b)
        await db.flush()
    return b


async def get_or_create_bin(db, block_id, floor, bn, sensor_id, fill):
    r = await db.execute(select(Bin).where(Bin.sensor_id == sensor_id))
    b = r.scalars().first()
    if not b:
        b = Bin(block_id=block_id, floor=floor, bin_number=bn,
                sensor_id=sensor_id, current_fill=fill)
        db.add(b)
        await db.flush()
    return b


async def main():
    async with Session() as db:
        # ── fetch existing users ──────────────────────────────
        def u(account):
            async def _get():
                r = await db.execute(select(User).where(User.username == account))
                return r.scalars().first()
            return _get

        admin     = await (u('admin'))()
        liwei     = await (u('liwei'))()
        zhangming = await (u('zhangming'))()
        wangfang  = await (u('wangfang'))()

        # ── blocks ────────────────────────────────────────────
        ba = await get_or_create_block(db, 'Block A', 5, 2)
        bb = await get_or_create_block(db, 'Block B', 4, 2)
        bc = await get_or_create_block(db, 'Block C', 3, 2)

        # ── bins (current_fill drives status: <60 normal, 60-89 warning, ≥90 full)
        bins_def = [
            (ba, 1, 1, 'SN-A101', 95), (ba, 1, 2, 'SN-A102', 45),
            (ba, 2, 1, 'SN-A201', 78), (ba, 2, 2, 'SN-A202', 30),
            (ba, 3, 1, 'SN-A301', 92), (ba, 3, 2, 'SN-A302', 55),
            (ba, 4, 1, 'SN-A401', 20), (ba, 4, 2, 'SN-A402', 68),
            (ba, 5, 1, 'SN-A501', 85), (ba, 5, 2, 'SN-A502', 10),
            (bb, 1, 1, 'SN-B101', 91), (bb, 1, 2, 'SN-B102', 40),
            (bb, 2, 1, 'SN-B201', 65), (bb, 2, 2, 'SN-B202', 88),
            (bb, 3, 1, 'SN-B301', 15), (bb, 3, 2, 'SN-B302', 72),
            (bb, 4, 1, 'SN-B401', 50), (bb, 4, 2, 'SN-B402', 96),
            (bc, 1, 1, 'SN-C101', 80), (bc, 1, 2, 'SN-C102', 25),
            (bc, 2, 1, 'SN-C201', 93), (bc, 2, 2, 'SN-C202', 60),
            (bc, 3, 1, 'SN-C301', 35), (bc, 3, 2, 'SN-C302', 77),
        ]
        bins = {}
        for blk, fl, bn, sid, fill in bins_def:
            bins[sid] = await get_or_create_bin(db, blk.id, fl, bn, sid, fill)

        # ── cleaner-block assignments ─────────────────────────
        existing = await db.execute(select(CleanerBlock))
        assigned = {(r.cleaner_id, r.block_id) for r in existing.scalars().all()}
        for cleaner, block in [
            (liwei, ba), (liwei, bb),
            (zhangming, bb), (zhangming, bc),
            (wangfang, bc), (wangfang, ba),
        ]:
            if (cleaner.id, block.id) not in assigned:
                db.add(CleanerBlock(cleaner_id=cleaner.id, block_id=block.id))
        await db.flush()

        # ── tasks ─────────────────────────────────────────────
        now = datetime.now()
        tasks = [
            # pending unassigned
            Task(bin_id=bins['SN-A101'].id, status='pending',
                 created_at=now - timedelta(hours=2)),
            Task(bin_id=bins['SN-B101'].id, status='pending',
                 created_at=now - timedelta(hours=1)),
            # pending assigned
            Task(bin_id=bins['SN-A301'].id, cleaner_id=liwei.id, status='pending',
                 created_at=now - timedelta(hours=3)),
            Task(bin_id=bins['SN-B402'].id, cleaner_id=wangfang.id, status='pending',
                 created_at=now - timedelta(minutes=90)),
            # in_progress
            Task(bin_id=bins['SN-A402'].id, cleaner_id=zhangming.id, status='in_progress',
                 created_at=now - timedelta(hours=4),
                 accepted_at=now - timedelta(minutes=45)),
            Task(bin_id=bins['SN-C201'].id, cleaner_id=wangfang.id, status='in_progress',
                 created_at=now - timedelta(hours=2),
                 accepted_at=now - timedelta(minutes=20)),
            # completed — awaiting admin score (shows in TaskScoring)
            Task(bin_id=bins['SN-A201'].id, cleaner_id=zhangming.id, status='completed',
                 created_at=now - timedelta(days=2),
                 accepted_at=now - timedelta(days=2) + timedelta(minutes=30),
                 completed_at=now - timedelta(days=2) + timedelta(minutes=90),
                 result='cleaned'),
            Task(bin_id=bins['SN-B202'].id, cleaner_id=liwei.id, status='completed',
                 created_at=now - timedelta(days=1),
                 accepted_at=now - timedelta(days=1) + timedelta(minutes=20),
                 completed_at=now - timedelta(days=1) + timedelta(minutes=70),
                 result='cleaned'),
            Task(bin_id=bins['SN-C302'].id, cleaner_id=wangfang.id, status='completed',
                 created_at=now - timedelta(days=3),
                 accepted_at=now - timedelta(days=3) + timedelta(minutes=40),
                 completed_at=now - timedelta(days=3) + timedelta(minutes=100),
                 result='false_alarm'),
            # rated
            Task(bin_id=bins['SN-B101'].id, cleaner_id=liwei.id, status='rated',
                 created_at=now - timedelta(days=5),
                 accepted_at=now - timedelta(days=5) + timedelta(hours=1),
                 completed_at=now - timedelta(days=5) + timedelta(hours=2),
                 result='cleaned', rating=5,
                 comment='Excellent work, very clean!',
                 rated_by=admin.id,
                 rated_at=now - timedelta(days=5) + timedelta(hours=3)),
            Task(bin_id=bins['SN-A301'].id, cleaner_id=wangfang.id, status='rated',
                 created_at=now - timedelta(days=4),
                 accepted_at=now - timedelta(days=4) + timedelta(minutes=30),
                 completed_at=now - timedelta(days=4) + timedelta(minutes=80),
                 result='cleaned', rating=4,
                 comment='Good job, on time',
                 rated_by=admin.id,
                 rated_at=now - timedelta(days=4) + timedelta(hours=5)),
            Task(bin_id=bins['SN-C201'].id, cleaner_id=zhangming.id, status='rated',
                 created_at=now - timedelta(days=6),
                 accepted_at=now - timedelta(days=6) + timedelta(hours=2),
                 completed_at=now - timedelta(days=6) + timedelta(hours=3),
                 result='cleaned', rating=3,
                 comment='Acceptable but could be faster',
                 rated_by=admin.id,
                 rated_at=now - timedelta(days=6) + timedelta(hours=4)),
        ]
        db.add_all(tasks)
        await db.commit()

    print('✓ Seed complete!')
    print('  Blocks : Block A / B / C')
    print('  Bins   : 24 (full/warning/normal mix)')
    print('  Tasks  : 4 pending, 2 in_progress, 3 completed, 3 rated')


asyncio.run(main())
