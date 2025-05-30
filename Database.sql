-- 1) Create database if not exists
USE master;
GO
IF DB_ID(N'DemoDB') IS NULL
    CREATE DATABASE DemoDB;
GO

USE DemoDB;
GO

-- 2) Drop existing objects if they exist

-- Triggers
IF OBJECT_ID(N'trg_emp_delete','TR') IS NOT NULL
    DROP TRIGGER trg_emp_delete;
GO
IF OBJECT_ID(N'trg_salary_change','TR') IS NOT NULL
    DROP TRIGGER trg_salary_change;
GO

-- Stored Procedures
IF OBJECT_ID(N'assign_employee_dept','P') IS NOT NULL
    DROP PROCEDURE assign_employee_dept;
GO
IF OBJECT_ID(N'add_department','P') IS NOT NULL
    DROP PROCEDURE add_department;
GO
IF OBJECT_ID(N'increase_salary','P') IS NOT NULL
    DROP PROCEDURE increase_salary;
GO

-- Tables
IF OBJECT_ID(N'employee_delete_audit','U') IS NOT NULL
    DROP TABLE employee_delete_audit;
GO
IF OBJECT_ID(N'salary_audit','U') IS NOT NULL
    DROP TABLE salary_audit;
GO
IF OBJECT_ID(N'employees','U') IS NOT NULL
    DROP TABLE employees;
GO
IF OBJECT_ID(N'departments','U') IS NOT NULL
    DROP TABLE departments;
GO

-- 3) Create tables

CREATE TABLE departments (
    dept_id   INT IDENTITY(1,1) PRIMARY KEY,
    name      NVARCHAR(100) NOT NULL
);
GO

CREATE TABLE employees (
    id       INT IDENTITY(1,1) PRIMARY KEY,
    name     NVARCHAR(100) NOT NULL,
    salary   DECIMAL(10,2) NOT NULL
);
GO

CREATE TABLE salary_audit (
    audit_id    INT IDENTITY(1,1) PRIMARY KEY,
    emp_id      INT NOT NULL,
    old_salary  DECIMAL(10,2) NULL,
    new_salary  DECIMAL(10,2) NULL,
    changed_at  DATETIME NOT NULL DEFAULT GETDATE(),
    change_desc NVARCHAR(200) NULL
);
GO

CREATE TABLE employee_delete_audit (
    audit_id   INT IDENTITY(1,1) PRIMARY KEY,
    emp_id     INT         NULL,
    name       NVARCHAR(100) NULL,
    salary     DECIMAL(10,2) NULL,
    deleted_at DATETIME     NOT NULL DEFAULT GETDATE()
);
GO

-- 4) Add foreign keys

ALTER TABLE employees
ADD dept_id INT NULL
    CONSTRAINT FK_emp_dept 
    FOREIGN KEY(dept_id) REFERENCES departments(dept_id);
GO

ALTER TABLE salary_audit
ADD CONSTRAINT FK_salary_audit_emp 
    FOREIGN KEY(emp_id) REFERENCES employees(id)
    ON DELETE CASCADE;
GO

-- 5) Create Stored Procedures

CREATE PROCEDURE increase_salary
    @emp_id INT,
    @amount DECIMAL(10,2)
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE employees
       SET salary = salary + @amount
     WHERE id = @emp_id;
END;
GO

CREATE PROCEDURE add_department
    @name NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO departments(name) VALUES(@name);
END;
GO

CREATE PROCEDURE assign_employee_dept
    @emp_id  INT,
    @dept_id INT
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE employees
       SET dept_id = @dept_id
     WHERE id = @emp_id;
END;
GO

-- 6) Create Triggers

CREATE TRIGGER trg_salary_change
ON employees
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO salary_audit(emp_id, old_salary, new_salary, changed_at, change_desc)
    SELECT
        d.id,
        d.salary,
        i.salary,
        GETDATE(),
        CONCAT(
          N'Lương: ',
          FORMAT(d.salary, 'N2', 'vi-VN'),
          N' → ',
          FORMAT(i.salary, 'N2', 'vi-VN')
        )
    FROM deleted d
    JOIN inserted i ON d.id = i.id;
END;
GO

CREATE TRIGGER trg_emp_delete
ON employees
AFTER DELETE
AS
BEGIN
    SET NOCOUNT ON;
    INSERT INTO employee_delete_audit(emp_id, name, salary, deleted_at)
    SELECT id, name, salary, GETDATE()
      FROM deleted;
END;
GO
