# Leader Role — Design Spec
Date: 2026-07-09

## Summary
Add a `leader` permission tier between `admin` and `cleaner`.
Leaders are field supervisors: they can monitor all data, assign tasks, and rate completed work, but cannot manage users, roles, or system configuration (bins/blocks).

## Permission Matrix

| Action | Admin | Leader | Cleaner |
|--------|-------|--------|---------|
| View dashboard / bins / blocks / work status | ✓ | ✓ | — |
| Assign tasks to cleaners | ✓ | ✓ | — |
| Rate completed tasks | ✓ | ✓ | — |
| Create / delete tasks | ✓ | — | — |
| Create / edit / delete bins & blocks | ✓ | — | — |
| Create / edit / delete users | ✓ | — | — |
| Manage roles | ✓ | — | — |
| Accept tasks / submit reports / clock in | — | — | ✓ |

## Backend Changes

### `core/deps.py`
Add a new dependency `get_current_admin_or_leader`:
```python
async def get_current_admin_or_leader(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "leader"):
        raise HTTPException(403, "Admin or Leader access required")
    return current_user
```

### `routers/tasks.py`
- `POST /api/tasks/{id}/assign` — change from `get_current_admin` → `get_current_admin_or_leader`
- `POST /api/tasks/{id}/rate`   — change from `get_current_admin` → `get_current_admin_or_leader`

All other task endpoints unchanged.

## Web Frontend Changes

### `src/types/index.ts`
```typescript
// Before
role: string
// After
role: 'admin' | 'leader' | 'cleaner'
```

### `src/layouts/MainLayout.tsx`
Hide "Users" and "Roles" nav items when `user.role === 'leader'`.

### Pages — hide write actions for leader
| Page | Hidden for leader |
|------|------------------|
| `Bins.tsx` | Create / Edit / Delete buttons |
| `Blocks.tsx` | Create / Edit / Delete buttons |
| `Users.tsx` | Create / Edit / Delete / Reset Password buttons |
| `Roles.tsx` | Create / Deactivate / Restore buttons |

Read access (view table data) remains available.

## Mobile App Changes

### `app/main.html`
Change the Admin tab visibility check:
```javascript
// Before
if (ME?.role !== 'admin') { hide admin tab }
// After
if (ME?.role !== 'admin' && ME?.role !== 'leader') { hide admin tab }
```
Leaders see the Admin Scoring tab; KPI tab is hidden for leaders (same as admins).

## Demo Data

Add one leader user to `scripts/init_db.py`:
```python
leader = User(
    name='Team Leader', username='leader',
    password_hash=hash_password('leader123'),
    role='leader', status='active',
)
```

## Out of Scope
- No new pages or API endpoints
- No changes to cleaner or admin existing behaviour
- No changes to the role management table (Leader already exists there as a display label)
