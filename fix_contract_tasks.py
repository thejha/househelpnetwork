import os
import sys
from flask import Flask
from config import config
from extensions import db
from models import Contract, TaskList, HelperProfile

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def fix_contract_tasks():
    """Add task IDs to a contract that has empty tasks"""
    app = create_app()
    
    with app.app_context():
        # Get all contracts with empty tasks
        contracts = Contract.query.filter(Contract.tasks == '').all()
        
        if not contracts:
            print("No contracts found with empty tasks.")
            return
        
        print(f"Found {len(contracts)} contracts with empty tasks.")
        
        # Get available tasks
        tasks = TaskList.query.all()
        if not tasks:
            print("No tasks found in the database.")
            return
        
        print(f"Available tasks:")
        for task in tasks:
            print(f"  ID: {task.id}, Name: {task.name}, Category: {task.category}")
        
        for contract in contracts:
            print(f"\nFIXING Contract ID: {contract.contract_id}")
            
            # Get helper profile for this contract
            helper = HelperProfile.query.get(contract.helper_profile_id)
            
            if not helper:
                print(f"  Helper not found for contract {contract.contract_id}")
                continue
                
            print(f"  Helper type: {helper.helper_type}")
            
            # Get tasks for this contract's helper type
            relevant_tasks = TaskList.query.filter_by(helper_type=helper.helper_type).limit(5).all()
            
            if not relevant_tasks:
                print(f"  No tasks found for helper_type: {helper.helper_type}")
                continue
            
            # Add the first few tasks to this contract
            task_ids = [str(task.id) for task in relevant_tasks]
            tasks_str = ','.join(task_ids)
            
            print(f"  Adding tasks: {tasks_str}")
            
            # Update the contract
            contract.tasks = tasks_str
            db.session.commit()
            print(f"  Contract updated successfully!")

if __name__ == "__main__":
    fix_contract_tasks() 