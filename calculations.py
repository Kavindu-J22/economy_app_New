from config import Config
import math

class CurrencyCalculator:
    def __init__(self):
        self.fees = Config.CURRENCY_FEES
        self.min_transaction = Config.MIN_TRANSACTION
        self.max_transaction = Config.MAX_TRANSACTION
    
    def calculate_fee(self, amount):
        """Calculate fee based on amount"""
        for fee_tier in self.fees:
            if fee_tier['min'] <= amount <= fee_tier['max']:
                return fee_tier['fee']
        return self.fees[-1]['fee']  # Default to highest tier
    
    def validate_transaction(self, amount):
        """Validate transaction amount"""
        if amount < self.min_transaction:
            return False, f"Minimum transaction amount is {self.min_transaction}"
        if amount > self.max_transaction:
            return False, f"Maximum transaction amount is {self.max_transaction}"
        return True, "Valid transaction"
    
    def calculate_conversion(self, amount, exchange_rate):
        """Calculate currency conversion with fees"""
        # Validate transaction
        is_valid, message = self.validate_transaction(amount)
        if not is_valid:
            return None, message
        
        # Calculate fee
        fee_percentage = self.calculate_fee(amount)
        fee_amount = amount * fee_percentage
        
        # Calculate conversion
        amount_after_fee = amount - fee_amount
        converted_amount = amount_after_fee * exchange_rate
        total_cost = amount  # Total cost is the original amount
        
        return {
            'original_amount': round(amount, 2),
            'fee_percentage': round(fee_percentage * 100, 2),
            'fee_amount': round(fee_amount, 2),
            'amount_after_fee': round(amount_after_fee, 2),
            'exchange_rate': round(exchange_rate, 6),
            'converted_amount': round(converted_amount, 2),
            'total_cost': round(total_cost, 2)
        }, "Success"


class InvestmentCalculator:
    def __init__(self):
        self.investment_types = Config.INVESTMENT_TYPES
    
    def validate_investment(self, investment_type, initial_lump_sum, monthly_investment):
        """Validate investment parameters"""
        if investment_type not in self.investment_types:
            return False, "Invalid investment type"
        
        plan = self.investment_types[investment_type]
        
        # Check minimum lump sum
        if initial_lump_sum < plan['min_lump_sum']:
            return False, f"Minimum initial investment for {plan['name']} is £{plan['min_lump_sum']}"
        
        # Check minimum monthly investment
        if monthly_investment < plan['min_monthly']:
            return False, f"Minimum monthly investment for {plan['name']} is £{plan['min_monthly']}"
        
        # Check maximum yearly investment
        yearly_investment = initial_lump_sum + (monthly_investment * 12)
        if yearly_investment > plan['max_yearly']:
            return False, f"Maximum yearly investment for {plan['name']} is £{plan['max_yearly']}"
        
        return True, "Valid investment"
    
    def calculate_investment_projection(self, investment_type, initial_lump_sum, monthly_investment):
        """Calculate investment projections for 1, 5, and 10 years"""
        # Validate investment
        is_valid, message = self.validate_investment(investment_type, initial_lump_sum, monthly_investment)
        if not is_valid:
            return None, message
        
        plan = self.investment_types[investment_type]
        
        projections = {}
        
        for years in [1, 5, 10]:
            # Calculate total invested
            total_invested = initial_lump_sum + (monthly_investment * 12 * years)
            
            # Calculate fees
            monthly_fee_rate = plan['monthly_fee']
            total_fees = 0
            
            # Fee on initial lump sum
            if initial_lump_sum > 0:
                total_fees += initial_lump_sum * monthly_fee_rate * 12 * years
            
            # Fee on monthly investments (average over time)
            monthly_total = 0
            for month in range(1, (12 * years) + 1):
                monthly_total += monthly_investment
                total_fees += monthly_total * monthly_fee_rate
            
            # Calculate returns (min and max scenarios)
            min_return_rate = plan['return_min']
            max_return_rate = plan['return_max']
            
            # Compound interest calculation for lump sum
            min_lump_value = initial_lump_sum * ((1 + min_return_rate) ** years)
            max_lump_value = initial_lump_sum * ((1 + max_return_rate) ** years)
            
            # Future value of annuity for monthly investments
            if min_return_rate > 0:
                min_monthly_value = monthly_investment * (((1 + min_return_rate) ** years - 1) / min_return_rate) * 12
            else:
                min_monthly_value = monthly_investment * 12 * years
            
            if max_return_rate > 0:
                max_monthly_value = monthly_investment * (((1 + max_return_rate) ** years - 1) / max_return_rate) * 12
            else:
                max_monthly_value = monthly_investment * 12 * years
            
            # Total values before fees and taxes
            min_total_before_tax = min_lump_value + min_monthly_value - total_fees
            max_total_before_tax = max_lump_value + max_monthly_value - total_fees
            
            # Calculate taxes
            min_profit = max(0, min_total_before_tax - total_invested)
            max_profit = max(0, max_total_before_tax - total_invested)
            
            min_tax = self.calculate_tax(min_profit, plan)
            max_tax = self.calculate_tax(max_profit, plan)
            
            # Final values after tax
            min_final_value = min_total_before_tax - min_tax
            max_final_value = max_total_before_tax - max_tax
            
            projections[f'year_{years}'] = {
                'min_value': round(min_final_value, 2),
                'max_value': round(max_final_value, 2),
                'min_profit': round(min_profit, 2),
                'max_profit': round(max_profit, 2),
                'total_fees': round(total_fees, 2),
                'min_tax': round(min_tax, 2),
                'max_tax': round(max_tax, 2),
                'total_invested': round(total_invested, 2)
            }
        
        return projections, "Success"
    
    def calculate_tax(self, profit, plan):
        """Calculate tax based on profit and plan type"""
        if profit <= 0:
            return 0
        
        tax = 0
        
        if plan.get('tax_rate'):
            # Simple tax rate (Basic and Plus plans)
            threshold = plan.get('tax_threshold', 0)
            if profit > threshold:
                tax = (profit - threshold) * plan['tax_rate']
        
        elif plan.get('tax_rates'):
            # Progressive tax rates (Managed plan)
            remaining_profit = profit
            thresholds = plan['tax_thresholds']
            rates = plan['tax_rates']
            
            for i, threshold in enumerate(thresholds):
                if remaining_profit > threshold:
                    if i == 0:
                        # First threshold
                        taxable_amount = min(remaining_profit - threshold, 
                                           thresholds[1] - threshold if len(thresholds) > 1 else remaining_profit - threshold)
                    else:
                        # Second threshold and beyond
                        taxable_amount = remaining_profit - threshold
                    
                    tax += taxable_amount * rates[i]
                    
                    if i < len(thresholds) - 1:
                        remaining_profit = max(0, remaining_profit - thresholds[i+1])
                    else:
                        break
        
        return max(0, tax)
