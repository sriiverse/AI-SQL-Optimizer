# 🧪 Advanced Testing Guide: Real AI Mode

Now that your app is powered by Google Gemini, it can handle complex logic. Use these scenarios to test its limits!

---

## 🚀 Mode 1: Query Optimizer
*Paste these bad queries into the "Input SQL Query" box and hit **Analyze**.*

### Case 1: The "Everything" Nightmare (Performance)
**Scenario:** A junior developer tries to get everything from a massive log table with an inefficient wildcard filter.
**Query:**
```sql
SELECT * 
FROM app_logs 
WHERE log_message LIKE '%error%' 
AND timestamp > '2023-01-01';
```
**What to look for:**
*   AI should warn about `SELECT *` (fetching unnecessary columns).
*   AI should warn about `LIKE '%error%'` (leading wildcard kills index usage).
*   AI might suggest using Full Text Search or a reversed index.

### Case 2: The Implicit Join Trap (Modern Standards)
**Scenario:** An old-school legacy query using implicit joins from the 90s.
**Query:**
```sql
SELECT u.name, o.id, p.title
FROM users u, orders o, products p
WHERE u.id = o.user_id 
AND o.product_id = p.id
AND u.status = 'active';
```
**What to look for:**
*   AI should recommend switching to explicit `INNER JOIN` syntax for readability and standard compliance.
*   AI might suggest indexes on `user_id` and `product_id`.

### Case 3: The N+1 Subquery Disaster (Architecture)
**Scenario:** Running a subquery for *every single row* in the users table.
**Query:**
```sql
SELECT 
    name, 
    (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
FROM users;
```
**What to look for:**
*   AI should identify this as a "Correlated Subquery" which is terrible for performance on large tables.
*   AI should suggest rewriting it as a `LEFT JOIN` with `GROUP BY`.

---

## ⚡ Mode 2: Text-to-SQL Generator
*Paste the Schema and then ask the Question.*

### Case 1: E-Commerce Analytics (Aggregations)
**Schema Context:**
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT,
    amount DECIMAL(10,2),
    created_at TIMESTAMP,
    status VARCHAR(20)
);
```
**Question:**
> "Calculate the total revenue per month for completed orders in 2023, sorted by the month with the highest revenue first."

**What to expect:**
*   AI should generate a query using `SUM(amount)`, `WHERE status = 'completed'`, and extract the month from `created_at` (e.g., `EXTRACT(MONTH FROM ...)` or `DATE_TRUNC`).

### Case 2: HR Hierarchy (Self-Joins)
**Schema Context:**
```sql
CREATE TABLE employees (
    id INT,
    name VARCHAR(100),
    salary INT,
    manager_id INT -- Points to another employee.id
);
```
**Question:**
> "List the names of all employees who earn more than their manager."

**What to expect:**
*   AI should figure out it needs a **Self-Join** (joining `employees` table to itself on `manager_id = id`).
*   Logic: `WHERE e.salary > m.salary`.

### Case 3: Complex Filtering & Window Functions
**Schema Context:**
```sql
CREATE TABLE students (
    id INT,
    name TEXT,
    class_id INT,
    score INT
);
```
**Question:**
> "Find the top 3 students in each class based on their score."

**What to expect:**
*   This is a hard one! AI should use a Window Function like `RANK()` or `ROW_NUMBER() OVER (PARTITION BY class_id ORDER BY score DESC)`.
*   A simpler AI might fail and just use `LIMIT 3`, but Gemini should correctly identify the "per class" requirement.
