"""
JARVIS Expense Tracker - Voice-controlled spending analytics
"""

import json
import os
from datetime import datetime

EXPENSE_FILE = 'expenses.json'

class ExpenseTracker:
    def __init__(self):
        self.expenses = self.load_expenses()
    
    def load_expenses(self):
        if os.path.exists(EXPENSE_FILE):
            try:
                with open(EXPENSE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {'expenses': []}
        return {'expenses': []}
    
    def save_expenses(self):
        with open(EXPENSE_FILE, 'w') as f:
            json.dump(self.expenses, f, indent=2)
    
    def add_expense(self, category, amount, description=''):
        """Log an expense"""
        expense = {
            'category': category,
            'amount': float(amount),
            'description': description,
            'date': datetime.now().isoformat()
        }
        self.expenses['expenses'].append(expense)
        self.save_expenses()
        return f"💰 Logged: {category} - ${amount}"
    
    def get_summary(self, period='today'):
        """Get spending summary"""
        if not self.expenses['expenses']:
            return "No expenses recorded"
        
        total = sum(exp['amount'] for exp in self.expenses['expenses'])
        by_category = {}
        
        for exp in self.expenses['expenses']:
            cat = exp['category']
            by_category[cat] = by_category.get(cat, 0) + exp['amount']
        
        summary = f"💵 Total Spending: ${total:.2f}\n"
        summary += "By Category:\n"
        for cat, amount in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            summary += f"  {cat}: ${amount:.2f}\n"
        
        return summary
    
    def get_balance(self):
        """Get remaining balance (assumes income entered as 'income' category with negative sign)"""
        total = sum(exp['amount'] for exp in self.expenses['expenses'])
        return f"Total Expenses: ${total:.2f}"
    
    def list_recent(self, limit=10):
        """Show recent expenses"""
        recent = self.expenses['expenses'][-limit:][::-1]
        
        if not recent:
            return "No expenses recorded"
        
        expense_list = "Recent Expenses:\n"
        for exp in recent:
            expense_list += f"  {exp['date'][:10]} - {exp['category']}: ${exp['amount']}"
            if exp['description']:
                expense_list += f" ({exp['description']})"
            expense_list += "\n"
        
        return expense_list

expense_tracker = ExpenseTracker()
