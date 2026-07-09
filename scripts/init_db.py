"""
One-time database initialization script.
Creates admin, demo cleaners, blocks, bins, roles and sample tasks.

Usage:
    docker exec waste_backend python3 /app/scripts/init_db.py
"""

import asyncio
from datetime import datetime, timedelta

from core.database import AsyncSessionLocal as async_session
from core.security import hash_password
from models.user import User
from models.block import Block
from models.bin import Bin
from models.role import Role
from models.task import Task
from models.cleaner_block import CleanerBlock


async def main():
    async with async_session() as db:

        # ── Roles ─────────────────────────────────────────────
        role_admin   = Role(name='Admin',   description='Full system access',       access_level='High',   permissions_count=20)
        role_cleaner = Role(name='Cleaner', description='Task execution only',      access_level='Low',    permissions_count=5)
        role_leader  = Role(name='Leader',  description='Team leader with reports', access_level='Medium', permissions_count=12)
        db.add_all([role_admin, role_cleaner, role_leader])
        await db.flush()

        # ── Users ─────────────────────────────────────────────
        admin = User(
            name='Admin', username='admin',
            password_hash=hash_password('admin123'),
            role='admin', status='active',
        )
        leader = User(
            name='Team Leader', username='leader',
            password_hash=hash_password('leader123'),
            role='leader', status='active',
        )
        c1 = User(name='Li Wei',     username='liwei',     password_hash=hash_password('cleaner123'), role='cleaner', zone='Zone A', shift='morning', status='active')
        c2 = User(name='Zhang Ming', username='zhangming', password_hash=hash_password('cleaner123'), role='cleaner', zone='Zone B', shift='evening', status='active')
        c3 = User(name='Wang Fang',  username='wangfang',  password_hash=hash_password('cleaner123'), role='cleaner', zone='Zone C', shift='morning', status='active')
        c4 = User(name='Chen Hao',   username='chenhao',   password_hash=hash_password('cleaner123'), role='cleaner', zone='Zone A', shift='night',   status='inactive')
        db.add_all([admin, leader, c1, c2, c3, c4])
        await db.flush()

        # ── Blocks ────────────────────────────────────────────
        ba = Block(name='Block A', total_floors=10, bins_per_floor=2)
        bb = Block(name='Block B', total_floors=8,  bins_per_floor=2)
        bc = Block(name='Block C', total_floors=12, bins_per_floor=2)
        bd = Block(name='Block D', total_floors=6,  bins_per_floor=2)
        be = Block(name='Block E', total_floors=10, bins_per_floor=2)
        db.add_all([ba, bb, bc, bd, be])
        await db.flush()

        # ── Bins ──────────────────────────────────────────────
        fills = [0, 15, 30, 45, 55, 65, 72, 80, 88, 91, 95, 98]
        bins = []
        snum = 1001
        for block in [ba, bb, bc, bd, be]:
            for floor in range(1, 5):
                for bn in range(1, 3):
                    fill = fills[(snum - 1001) % len(fills)]
                    bins.append(Bin(
                        block_id=block.id, floor=floor, bin_number=bn,
                        sensor_id=f'#{snum}', current_fill=fill,
                    ))
                    snum += 1
        db.add_all(bins)
        await db.flush()

        # ── Cleaner-Block assignments ──────────────────────────
        db.add_all([
            CleanerBlock(cleaner_id=c1.id, block_id=ba.id),
            CleanerBlock(cleaner_id=c1.id, block_id=bb.id),
            CleanerBlock(cleaner_id=c2.id, block_id=bc.id),
            CleanerBlock(cleaner_id=c2.id, block_id=bd.id),
            CleanerBlock(cleaner_id=c3.id, block_id=be.id),
        ])
        await db.flush()

        # ── Tasks ─────────────────────────────────────────────
        now = datetime.now()
        db.add_all([
            # pending unassigned
            Task(bin_id=bins[0].id, status='pending',
                 created_at=now - timedelta(minutes=40)),
            Task(bin_id=bins[9].id, status='pending',
                 created_at=now - timedelta(minutes=25)),
            # pending assigned
            Task(bin_id=bins[1].id, cleaner_id=c1.id, status='pending',
                 created_at=now - timedelta(minutes=20)),
            # in_progress
            Task(bin_id=bins[2].id, cleaner_id=c2.id, status='in_progress',
                 created_at=now - timedelta(hours=1),
                 accepted_at=now - timedelta(minutes=50)),
            Task(bin_id=bins[10].id, cleaner_id=c1.id, status='in_progress',
                 created_at=now - timedelta(hours=2),
                 accepted_at=now - timedelta(hours=1, minutes=30)),
            # completed (awaiting rating)
            Task(bin_id=bins[3].id, cleaner_id=c3.id, status='completed',
                 created_at=now - timedelta(hours=3),
                 accepted_at=now - timedelta(hours=2, minutes=30),
                 completed_at=now - timedelta(hours=1),
                 result='cleaned'),
            Task(bin_id=bins[5].id, cleaner_id=c2.id, status='completed',
                 created_at=now - timedelta(hours=4),
                 accepted_at=now - timedelta(hours=3),
                 completed_at=now - timedelta(hours=2),
                 result='false_alarm'),
            # rated
            Task(bin_id=bins[4].id, cleaner_id=c1.id, status='rated',
                 created_at=now - timedelta(days=1),
                 accepted_at=now - timedelta(hours=23),
                 completed_at=now - timedelta(hours=22),
                 result='cleaned',
                 rating=5, comment='Excellent work, bin area left spotless',
                 rated_by=admin.id, rated_at=now - timedelta(hours=21)),
            Task(bin_id=bins[6].id, cleaner_id=c2.id, status='rated',
                 created_at=now - timedelta(days=2),
                 accepted_at=now - timedelta(days=1, hours=23),
                 completed_at=now - timedelta(days=1, hours=22),
                 result='damaged',
                 rating=3, comment='Bin damaged, maintenance scheduled',
                 rated_by=admin.id, rated_at=now - timedelta(days=1, hours=21)),
            Task(bin_id=bins[7].id, cleaner_id=c3.id, status='rated',
                 created_at=now - timedelta(days=3),
                 accepted_at=now - timedelta(days=2, hours=23),
                 completed_at=now - timedelta(days=2, hours=22),
                 result='cleaned',
                 rating=4, comment='Good job',
                 rated_by=admin.id, rated_at=now - timedelta(days=2, hours=21)),
        ])

        await db.commit()

    print('Database initialized successfully!')
    print('  Admin:    admin / admin123')
    print('  Leader:   leader / leader123')
    print('  Cleaners: liwei / zhangming / wangfang (password: cleaner123)')


asyncio.run(main())
