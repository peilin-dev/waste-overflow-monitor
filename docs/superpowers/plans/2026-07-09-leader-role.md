# Leader Role Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `leader` permission tier that can monitor data, assign tasks, and rate tasks — but cannot manage users, roles, or system configuration.

**Architecture:** Add a new `get_current_admin_or_leader` FastAPI dependency for the two task endpoints that leaders need; add role-aware rendering to the React frontend so leaders see read-only views of config pages and a filtered nav; update the PWA app to show the Admin Scoring tab to leaders.

**Tech Stack:** Python/FastAPI (backend), React 18/TypeScript (web frontend), Vanilla JS PWA (mobile app)

## Global Constraints

- Backend: only `routers/tasks.py` endpoints change — all other routers stay as-is
- Frontend: use `useAuthStore()` to read `user.role`; no new state or context needed
- No new pages, no new API endpoints
- Leader cannot access cleaner-only actions (accept task, submit report, clock in)
- Mobile app: leader sees Admin Scoring tab; KPI tab hidden (same behaviour as admin)

---

### Task 1: Backend — Add `get_current_admin_or_leader` dependency

**Files:**
- Modify: `E:/project/waste-overflow-monitor/core/deps.py`
- Modify: `E:/project/waste-overflow-monitor/routers/tasks.py`

**Interfaces:**
- Produces: `get_current_admin_or_leader` — async FastAPI dependency, same signature as `get_current_admin`, raises HTTP 403 if `user.role not in ("admin", "leader")`

- [ ] **Step 1: Add the new dependency to `core/deps.py`**

Open `core/deps.py`. After the `get_current_admin` function (line 70–78), add:

```python
async def get_current_admin_or_leader(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure the current user has admin or leader role."""
    if current_user.role not in ("admin", "leader"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Leader access required",
        )
    return current_user
```

- [ ] **Step 2: Import and use in `routers/tasks.py`**

At the top of `routers/tasks.py`, the import line currently reads:
```python
from core.deps import get_current_user, get_current_admin
```
Change it to:
```python
from core.deps import get_current_user, get_current_admin, get_current_admin_or_leader
```

- [ ] **Step 3: Update the `assign_task` endpoint**

Find the `assign_task` function (around line 89). Change its dependency from:
```python
_: User = Depends(get_current_admin),
```
to:
```python
_: User = Depends(get_current_admin_or_leader),
```

- [ ] **Step 4: Update the `rate_task` endpoint**

Find the `rate_task` function (around line 202). Change its dependency from:
```python
current_admin: User = Depends(get_current_admin),
```
to:
```python
current_admin: User = Depends(get_current_admin_or_leader),
```

- [ ] **Step 5: Manual verify — start backend and test**

```bash
cd E:/project/waste-overflow-monitor
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs`.
- Login as a user with `role='leader'` (add one manually to DB for now, or use seed in Task 6).
- Confirm `POST /api/tasks/{id}/assign` returns 200 for leader token.
- Confirm `POST /api/tasks/{id}/rate` returns 200 for leader token.
- Confirm `POST /api/tasks` (create) returns 403 for leader token.
- Confirm `DELETE /api/tasks/{id}` returns 403 for leader token.

---

### Task 2: Frontend — Update User type to include `'leader'`

**Files:**
- Modify: `E:/front/waste-monitor-web/src/types/index.ts`

**Interfaces:**
- Produces: `User.role` typed as `'admin' | 'leader' | 'cleaner'` — all pages that check `user?.role` benefit automatically

- [ ] **Step 1: Update the role field in the `User` interface**

Open `src/types/index.ts`. Find the `User` interface (line 2). Change:
```typescript
  role: string
```
to:
```typescript
  role: 'admin' | 'leader' | 'cleaner'
```

- [ ] **Step 2: Update `UserCreate` interface**

In the same file, find `UserCreate` (line 16). Change:
```typescript
  role: string
```
to:
```typescript
  role: 'admin' | 'leader' | 'cleaner'
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd E:/front/waste-monitor-web
npm run build
```
Expected: build succeeds with no type errors.

---

### Task 3: Web Frontend — Filter navigation and role label for leader

**Files:**
- Modify: `E:/front/waste-monitor-web/src/layouts/MainLayout.tsx`

**Interfaces:**
- Consumes: `user.role` from `useAuthStore()` — already available as `user` in the component

- [ ] **Step 1: Import `useAuthStore` role into sidebar rendering**

`user` is already destructured from `useAuthStore()` at line 44. No new import needed.

- [ ] **Step 2: Filter `NAV_SYSTEM` for leaders**

Find the `sidebarContent` block. The System nav section currently renders:
```tsx
<div style={{ fontSize: 10, ... }}>System</div>
{NAV_SYSTEM.map(item => <NavItem key={item.key} item={item} />)}
```

Replace with:
```tsx
{user?.role !== 'leader' && (
  <>
    <div style={{ fontSize: 10, fontWeight: 700, color: '#999', letterSpacing: '0.06em', textTransform: 'uppercase', margin: '14px 8px 8px' }}>System</div>
    {NAV_SYSTEM.map(item => <NavItem key={item.key} item={item} />)}
  </>
)}
```

- [ ] **Step 3: Update role label in the topbar**

Find the topbar section (around line 189–193):
```tsx
<span style={{ fontSize: 10, color: '#999' }}>Administrator</span>
```
Replace with:
```tsx
<span style={{ fontSize: 10, color: '#999' }}>
  {user?.role === 'leader' ? 'Leader' : 'Administrator'}
</span>
```

- [ ] **Step 4: Manual verify**

Start the frontend dev server:
```bash
cd E:/front/waste-monitor-web
npm run dev
```
- Log in as a leader user.
- Confirm "Blocks & Bins" and "Roles" items are absent from the sidebar.
- Confirm topbar shows "Leader" instead of "Administrator".
- Confirm admin user still sees the full System section.

---

### Task 4: Web Frontend — Hide write actions in config pages for leader

**Files:**
- Modify: `E:/front/waste-monitor-web/src/pages/Bins.tsx`
- Modify: `E:/front/waste-monitor-web/src/pages/Blocks.tsx`
- Modify: `E:/front/waste-monitor-web/src/pages/Users.tsx`
- Modify: `E:/front/waste-monitor-web/src/pages/Roles.tsx`

**Interfaces:**
- Consumes: `useAuthStore` — import `{ useAuthStore }` from `@/store/authStore` in each page

- [ ] **Step 1: `Bins.tsx` — hide Add / Edit / Delete for leader**

Add import at the top of `Bins.tsx`:
```typescript
import { useAuthStore } from '@/store/authStore'
```

Inside the `Bins()` component body, after existing state declarations, add:
```typescript
const { user } = useAuthStore()
const isLeader = user?.role === 'leader'
```

Find the "Add Bin" button (look for `onClick={openCreate}` or similar "Add" / "Create" button). Wrap it:
```tsx
{!isLeader && (
  <button onClick={openCreate}>Add Bin</button>
)}
```

Find the Edit and Delete action buttons in the table row. Wrap both:
```tsx
{!isLeader && (
  <>
    <button onClick={() => openEdit(bin)}>Edit</button>
    <Popconfirm onConfirm={() => handleDelete(bin.id)}>
      <button>Delete</button>
    </Popconfirm>
  </>
)}
```

- [ ] **Step 2: `Blocks.tsx` — hide Save / edit inputs for leader**

Add import:
```typescript
import { useAuthStore } from '@/store/authStore'
```

Inside `Blocks()` component body:
```typescript
const { user } = useAuthStore()
const isLeader = user?.role === 'leader'
```

Find the Save button and the editable input fields. The block table has inline editing — for leaders, render plain text instead of inputs, and hide the Save/Cancel buttons:

For each editable cell (name, total_floors, bins_per_floor), change from:
```tsx
<input value={getValue(block, 'name')} onChange={...} />
```
to:
```tsx
{isLeader
  ? <span>{getValue(block, 'name')}</span>
  : <input value={getValue(block, 'name')} onChange={...} />
}
```

Wrap the Save / Cancel / Add Block button group:
```tsx
{!isLeader && (
  <div>
    <button onClick={handleSave}>Save</button>
    <button onClick={handleCancel}>Cancel</button>
    <button onClick={openCreate}>Add Block</button>
  </div>
)}
```

- [ ] **Step 3: `Users.tsx` — hide Add / Edit / Delete / Reset Password for leader**

Add import:
```typescript
import { useAuthStore } from '@/store/authStore'
```

Inside `Users()` component body:
```typescript
const { user } = useAuthStore()
const isLeader = user?.role === 'leader'
```

Wrap the "Add User" / "Create" button:
```tsx
{!isLeader && <button onClick={openCreate}>Add User</button>}
```

In the table row action column, wrap Edit, Delete, and Reset Password buttons:
```tsx
{!isLeader && (
  <>
    <button onClick={() => openEdit(u)}>Edit</button>
    <button onClick={() => setResetModal(u)}>Reset Password</button>
    <Popconfirm onConfirm={() => handleDelete(u.id)}>
      <button>Delete</button>
    </Popconfirm>
  </>
)}
```

- [ ] **Step 4: `Roles.tsx` — hide Create / Deactivate / Restore for leader**

Add import:
```typescript
import { useAuthStore } from '@/store/authStore'
```

Inside `Roles()` component body:
```typescript
const { user } = useAuthStore()
const isLeader = user?.role === 'leader'
```

Wrap the "Add Role" button:
```tsx
{!isLeader && <button onClick={openCreate}>Add Role</button>}
```

Wrap Deactivate and Restore action buttons in the table:
```tsx
{!isLeader && (
  <>
    <button onClick={() => handleDeactivate(role.id)}>Deactivate</button>
    <button onClick={() => handleRestore(role.id)}>Restore</button>
  </>
)}
```

- [ ] **Step 5: Manual verify all four pages**

Log in as leader. Confirm:
- Bins page: table is visible, no Add/Edit/Delete buttons
- Blocks page: table is visible, all cells read-only, no Save/Add buttons
- Users page: table is visible, no Add/Edit/Delete/Reset buttons
- Roles page: table is visible, no Add/Deactivate/Restore buttons

Log in as admin. Confirm all buttons are still present.

---

### Task 5: Mobile App — Show Admin Scoring tab for leader

**Files:**
- Modify: `E:/front/waste-monitor-web/app/main.html`

**Interfaces:**
- Consumes: `ME.role` — already available as the `ME` variable in the init block

- [ ] **Step 1: Update tab visibility logic in `app/main.html`**

In `main.html`, find the init block near the bottom (around line 934–947):
```javascript
if (ME?.role !== 'admin') {
    document.getElementById('nav-admin').style.display = 'none';
} else {
    document.getElementById('nav-kpi').style.display = 'none';
}
```

Replace with:
```javascript
if (ME?.role === 'cleaner') {
    document.getElementById('nav-admin').style.display = 'none';
} else {
    // admin or leader: hide KPI tab, show Admin Scoring tab
    document.getElementById('nav-kpi').style.display = 'none';
}
```

- [ ] **Step 2: Manual verify**

Open `http://localhost:5173/app/` (or deployed URL).
- Log in as leader → Admin Scoring tab visible, KPI tab hidden.
- Log in as cleaner → KPI tab visible, Admin Scoring tab hidden.
- Log in as admin → Admin Scoring tab visible, KPI tab hidden (unchanged).

---

### Task 6: Demo data — Add leader seed user

**Files:**
- Modify: `E:/project/waste-overflow-monitor/scripts/init_db.py`

- [ ] **Step 1: Add leader user to the init script**

Open `scripts/init_db.py`. Find the Users section (around line 33). After the `admin` user, add:
```python
leader = User(
    name='Team Leader', username='leader',
    password_hash=hash_password('leader123'),
    role='leader', status='active',
)
```

Add `leader` to the `db.add_all` call:
```python
db.add_all([admin, leader, c1, c2, c3, c4])
```

Update the print statement at the bottom:
```python
print('  Leader:   leader / leader123')
```

- [ ] **Step 2: Re-run init script on a fresh database to verify**

```bash
docker exec waste_backend python3 /app/scripts/init_db.py
```

Expected output includes:
```
Database initialized successfully!
  Admin:    admin / admin123
  Leader:   leader / leader123
  Cleaners: liwei / zhangming / wangfang (password: cleaner123)
```

- [ ] **Step 3: End-to-end smoke test**

1. Log in to web admin as `leader / leader123`
   - Dashboard ✓, Work Status ✓, Tasks ✓, Task Scoring ✓ visible
   - Employees (read-only, no add/edit/delete) ✓
   - No "Blocks & Bins" or "Roles" in sidebar ✓
2. Via API (curl or Swagger): confirm leader can call `POST /api/tasks/{id}/assign` ✓
3. Via API: confirm leader can call `POST /api/tasks/{id}/rate` ✓
4. Via API: confirm leader gets 403 on `POST /api/tasks` (create) ✓
5. Log in to mobile app as `leader / leader123`
   - Admin Scoring tab visible ✓
   - KPI tab hidden ✓
