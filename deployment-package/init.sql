-- AI Development Team Database Schema
-- PostgreSQL initialization script

-- Agent runs table - tracks each AI execution
CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) UNIQUE NOT NULL,
    trigger_type VARCHAR(50) NOT NULL, -- push, pr, issue, manual
    trigger_data JSONB,
    role VARCHAR(50) NOT NULL, -- backend, frontend, qa, devops, security
    status VARCHAR(50) NOT NULL, -- processing, completed, failed
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent actions table - logs GitHub actions taken
CREATE TABLE IF NOT EXISTS agent_actions (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(100) NOT NULL REFERENCES agent_runs(run_id),
    action_type VARCHAR(50) NOT NULL, -- create_branch, commit, pr, comment
    resource VARCHAR(255), -- GitHub URL or identifier
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent memory table - stores repository context and preferences
CREATE TABLE IF NOT EXISTS agent_memory (
    id SERIAL PRIMARY KEY,
    repo VARCHAR(255) NOT NULL,
    key VARCHAR(255) NOT NULL,
    value JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repo, key)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_runs_created_at ON agent_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);
CREATE INDEX IF NOT EXISTS idx_agent_runs_role ON agent_runs(role);
CREATE INDEX IF NOT EXISTS idx_agent_actions_run_id ON agent_actions(run_id);
CREATE INDEX IF NOT EXISTS idx_agent_memory_repo ON agent_memory(repo);

-- Update trigger for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_agent_runs_updated_at 
    BEFORE UPDATE ON agent_runs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_memory_updated_at 
    BEFORE UPDATE ON agent_memory 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();