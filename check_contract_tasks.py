import os
import sys
from flask import Flask
from config import config
from extensions import db
from models import Contract, TaskList

def create_app(config_name='development'):
    """Factory function to create and configure the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app

def check_contract_tasks():
    """Check if contract tasks are properly saved"""
    app = create_app()
    
    with app.app_context():
        # Get all contracts
        contracts = Contract.query.all()
        
        if not contracts:
            print("No contracts found in the database.")
            return
        
        for contract in contracts:
            print(f"Contract ID: {contract.contract_id}")
            print(f"Tasks (raw): {contract.tasks}")
            
            # Split task IDs
            task_ids = contract.tasks.split(',') if contract.tasks else []
            print(f"Task IDs: {task_ids}")
            
            # Get task details
            tasks = TaskList.query.filter(TaskList.id.in_(task_ids)).all() if task_ids else []
            
            if tasks:
                print("Tasks found:")
                for task in tasks:
                    print(f"  ID: {task.id}, Name: {task.name}, Category: {task.category}")
            else:
                print("No tasks found for this contract!")
            
            print("-" * 50)

if __name__ == "__main__":
    check_contract_tasks() 