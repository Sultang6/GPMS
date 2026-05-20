-- GPMS PostgreSQL DDL
CREATE TYPE user_role AS ENUM ('Student', 'Supervisor', 'Admin');
CREATE TYPE project_status AS ENUM ('Pending', 'Approved', 'Active', 'Completed');
CREATE TYPE report_type AS ENUM ('Proposal', 'Midterm', 'Final');

CREATE TABLE projects (
    project_id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status project_status NOT NULL DEFAULT 'Pending',
    supervisor_id BIGINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    project_id BIGINT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_users_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE SET NULL -- Project has many students
);

ALTER TABLE projects
    ADD CONSTRAINT fk_projects_supervisor
    FOREIGN KEY (supervisor_id) REFERENCES users(user_id) ON DELETE SET NULL; -- Supervisor oversees many projects

CREATE TABLE submissions (
    submission_id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    student_id BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    report_type report_type NOT NULL,
    grade NUMERIC(5,2) NULL,
    feedback TEXT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_submissions_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE, -- Project has many submissions
    CONSTRAINT fk_submissions_student
        FOREIGN KEY (student_id) REFERENCES users(user_id) -- Student uploads many submissions
);

CREATE TABLE messages (
    message_id BIGSERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL,
    project_id BIGINT NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_messages_sender
        FOREIGN KEY (sender_id) REFERENCES users(user_id), -- User sends many messages
    CONSTRAINT fk_messages_project
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE -- Project has many chat messages
);

CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action_description VARCHAR(500) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_audit_logs_user
        FOREIGN KEY (user_id) REFERENCES users(user_id) -- User can generate many audit logs
);

CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_project_id ON users(project_id);
CREATE INDEX ix_projects_supervisor_id ON projects(supervisor_id);
CREATE INDEX ix_submissions_project_id ON submissions(project_id);
CREATE INDEX ix_submissions_student_id ON submissions(student_id);
CREATE INDEX ix_messages_project_id ON messages(project_id);
CREATE INDEX ix_messages_sender_id ON messages(sender_id);
CREATE INDEX ix_audit_logs_user_id ON audit_logs(user_id);

