-- 演示数据脚本（答辩前跑一次重置数据）
-- 用法：Navicat 新建查询 → 粘贴 → 运行

-- 清空任务和清洁工楼栋分配（保留用户和楼栋/垃圾桶基础数据）
DELETE FROM task;
DELETE FROM cleaner_block;

-- 清洁工楼栋分配
INSERT INTO cleaner_block (cleaner_id, block_id) VALUES
(1001, 1), (1001, 2),
(1002, 3), (1002, 4),
(1003, 5), (1003, 6);

-- pending（未指派）
INSERT INTO task (bin_id, cleaner_id, status, created_at) VALUES
(13, NULL,  'pending', NOW() - INTERVAL 30 MINUTE);

-- pending（已指派）
INSERT INTO task (bin_id, cleaner_id, status, created_at) VALUES
(15, 1001, 'pending', NOW() - INTERVAL 20 MINUTE);

-- in_progress
INSERT INTO task (bin_id, cleaner_id, status, created_at, accept_time) VALUES
(16, 1002, 'in_progress', NOW() - INTERVAL 1 HOUR, NOW() - INTERVAL 45 MINUTE);

-- completed（等待评分）
INSERT INTO task (bin_id, cleaner_id, status, created_at, accept_time, complete_time, result, photos) VALUES
(17, 1003, 'completed', NOW() - INTERVAL 2 HOUR, NOW() - INTERVAL 1 HOUR, NOW() - INTERVAL 30 MINUTE,
 'cleaned', JSON_ARRAY('https://example.com/photo1.jpg'));

-- rated（评分完成）
INSERT INTO task (bin_id, cleaner_id, status, created_at, accept_time, complete_time, result, photos, rating, comment, rated_by, rated_at) VALUES
(1, 1001, 'rated', NOW() - INTERVAL 1 DAY, NOW() - INTERVAL 23 HOUR, NOW() - INTERVAL 22 HOUR,
 'cleaned', JSON_ARRAY('https://example.com/photo2.jpg'),
 5, 'Excellent work, bin area left clean', 1006, NOW() - INTERVAL 21 HOUR),

(5, 1002, 'rated', NOW() - INTERVAL 2 DAY, NOW() - INTERVAL 47 HOUR, NOW() - INTERVAL 46 HOUR,
 'damaged', JSON_ARRAY('https://example.com/damage.jpg'),
 3, 'Bin damaged, maintenance scheduled', 1006, NOW() - INTERVAL 45 HOUR),

(8, 1003, 'rated', NOW() - INTERVAL 3 DAY, NOW() - INTERVAL 71 HOUR, NOW() - INTERVAL 70 HOUR,
 'cleaned', JSON_ARRAY('https://example.com/photo3.jpg'),
 4, 'Good job', 1006, NOW() - INTERVAL 69 HOUR);
