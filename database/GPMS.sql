-- GPMS Database Schema (PostgreSQL)

-- 1. Create 'projects' table first without the 'supervisor_id' foreign key
-- to handle the circular dependency between 'users' and 'projects'.
CREATE TABLE projects (
    project_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) CHECK (status IN ('Pending', 'Approved', 'Active', 'Completed')) DEFAULT 'Pending',
    supervisor_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Create 'users' table and set up the foreign key to 'projects'.
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) CHECK (role IN ('Student', 'Supervisor', 'Admin')) NOT NULL,
    project_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: 1:N between projects and Students (users table). Student belongs to one project.
    CONSTRAINT fk_users_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL
);

-- 3. Alter 'projects' table to add the 'supervisor_id' foreign key.
-- FK: 1:N between Supervisor (users table) and projects. Supervisor can oversee multiple projects.
ALTER TABLE projects
    ADD CONSTRAINT fk_projects_supervisor FOREIGN KEY (supervisor_id) REFERENCES users(user_id) ON DELETE SET NULL;

-- 4. Create 'submissions' table.
CREATE TABLE submissions (
    submission_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    student_id INT NOT NULL,
    file_path TEXT NOT NULL,
    report_type VARCHAR(20) CHECK (report_type IN ('Proposal', 'Midterm', 'Final')) NOT NULL,
    grade DECIMAL(5,2) NULL,
    feedback TEXT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: 1:N between projects and submissions. Project has multiple report submissions.
    CONSTRAINT fk_submissions_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    -- FK: 1:N between users (students) and submissions. Track which student uploaded the file.
    CONSTRAINT fk_submissions_student FOREIGN KEY (student_id) REFERENCES users(user_id)
);

-- 5. Create 'messages' table for the Group Chat Module.
CREATE TABLE messages (
    message_id SERIAL PRIMARY KEY,
    sender_id INT NOT NULL,
    project_id INT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: 1:N between users and messages. A user sends multiple messages.
    CONSTRAINT fk_messages_sender FOREIGN KEY (sender_id) REFERENCES users(user_id),
    -- FK: 1:N between projects and messages. Project acts as a chat room.
    CONSTRAINT fk_messages_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- 6. Create 'audit_logs' table.
CREATE TABLE audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    action_description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: 1:N between users and audit_logs. Track admin/supervisor actions.
    CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 7. Create 'project_references' table.
CREATE TABLE project_references (
    reference_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    url_or_path TEXT NOT NULL,
    reference_type VARCHAR(20) CHECK (reference_type IN ('Link', 'Document')) NOT NULL,
    added_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: Reference belongs to a project
    CONSTRAINT fk_references_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    -- FK: Track who added the reference
    CONSTRAINT fk_references_added_by FOREIGN KEY (added_by) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 8. Create 'project_tasks' table (Kanban Board).
CREATE TABLE project_tasks (
    task_id SERIAL PRIMARY KEY,
    project_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) CHECK (status IN ('To Do', 'In Progress', 'Done')) DEFAULT 'To Do',
    assigned_to INT NULL,
    due_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: Task belongs to a project
    CONSTRAINT fk_tasks_project FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    -- FK: Task is assigned to a specific user (student/supervisor)
    CONSTRAINT fk_tasks_assigned_to FOREIGN KEY (assigned_to) REFERENCES users(user_id) ON DELETE SET NULL
);

-- 9. Create 'notifications' table.
CREATE TABLE notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- FK: Notification belongs to a user
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 10. Add appropriate indexing for frequently searched columns.
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_project_id ON users(project_id);
CREATE INDEX idx_projects_supervisor_id ON projects(supervisor_id);
CREATE INDEX idx_submissions_project_id ON submissions(project_id);
CREATE INDEX idx_submissions_student_id ON submissions(student_id);
CREATE INDEX idx_messages_project_id ON messages(project_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

-- New Indexes for the added tables
CREATE INDEX idx_references_project_id ON project_references(project_id);
CREATE INDEX idx_tasks_project_id ON project_tasks(project_id);
CREATE INDEX idx_tasks_assigned_to ON project_tasks(assigned_to);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
