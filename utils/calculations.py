import pandas as pd
import numpy as np

def calculate_current_revenue(df):
    """
    Calculate current revenue from marketplace fees.

    Args:
        df (pd.DataFrame): Restaurant brands dataset with Total_Score

    Returns:
        pd.DataFrame: DataFrame with current revenue and tier assignment
    """
    df_rev = df.copy()

    # Calculate current annual revenue
    df_rev['Current_Revenue'] = (
        df_rev['Annualized Trips'] *
        df_rev['Avg. Basket Size'] *
        df_rev['Marketplace Fee']
    )

    # Assign tiers based on rank (requires Total_Score)
    if 'Total_Score' in df_rev.columns:
        df_rev['Rank'] = df_rev['Total_Score'].rank(ascending=False, method='min').astype(int)

        # Assign tiers
        df_rev['Tier'] = 'C-tier'  # Default
        df_rev.loc[df_rev['Rank'] <= 10, 'Tier'] = 'S-tier'
        df_rev.loc[(df_rev['Rank'] > 10) & (df_rev['Rank'] <= 50), 'Tier'] = 'A-tier'
        df_rev.loc[(df_rev['Rank'] > 50) & (df_rev['Rank'] <= 150), 'Tier'] = 'B-tier'
    else:
        # Fallback if no scoring available
        df_rev['Rank'] = range(1, len(df_rev) + 1)
        df_rev['Tier'] = 'C-tier'

    return df_rev

def apply_fee_changes(df, s_tier_fee=0.15, a_tier_fee=0.20, b_tier_fee=0.22, c_tier_fee=0.25,
                     elasticity_decrease=0.20, elasticity_increase=0.10):
    """
    Apply fee changes based on tier and calculate volume impact.

    Args:
        df (pd.DataFrame): DataFrame with Tier column
        s_tier_fee (float): New fee for S-tier (default 15%)
        a_tier_fee (float): New fee for A-tier (default 20%)
        b_tier_fee (float): New fee for B-tier (default 22%)
        c_tier_fee (float): New fee for C-tier (default 25%)
        elasticity_decrease (float): Volume increase per 5% fee decrease (default 0.20 = 20%)
        elasticity_increase (float): Volume decrease per 5% fee increase (default 0.10 = 10%)

    Returns:
        pd.DataFrame: DataFrame with new fees and adjusted volumes
    """
    df_modified = df.copy()

    # Map tier to new fee
    tier_fees = {
        'S-tier': s_tier_fee,
        'A-tier': a_tier_fee,
        'B-tier': b_tier_fee,
        'C-tier': c_tier_fee
    }

    df_modified['New_Fee'] = df_modified['Tier'].map(tier_fees)

    # Calculate fee change percentage
    df_modified['Fee_Change_Pct'] = (
        (df_modified['New_Fee'] - df_modified['Marketplace Fee']) / df_modified['Marketplace Fee']
    )

    # Calculate volume impact based on elasticity
    # For fee decreases (negative change), volume increases
    # For fee increases (positive change), volume decreases

    def calculate_volume_change(fee_change):
        if fee_change < 0:  # Fee decrease
            # Each 5% decrease → elasticity_decrease% volume increase
            volume_change = -(fee_change / 0.05) * elasticity_decrease
        else:  # Fee increase
            # Each 5% increase → elasticity_increase% volume decrease
            volume_change = -(fee_change / 0.05) * elasticity_increase
        return volume_change

    df_modified['Volume_Change_Pct'] = df_modified['Fee_Change_Pct'].apply(calculate_volume_change)

    # Calculate new trips
    df_modified['New_Trips'] = (
        df_modified['Annualized Trips'] * (1 + df_modified['Volume_Change_Pct'])
    )

    return df_modified

def calculate_new_revenue(df_modified):
    """
    Calculate new revenue after fee changes.

    Args:
        df_modified (pd.DataFrame): DataFrame with New_Fee and New_Trips

    Returns:
        pd.DataFrame: DataFrame with new revenue calculated
    """
    df_new = df_modified.copy()

    # Calculate new revenue
    df_new['New_Revenue'] = (
        df_new['New_Trips'] *
        df_new['Avg. Basket Size'] *
        df_new['New_Fee']
    )

    return df_new

def calculate_revenue_delta(df_with_revenue):
    """
    Calculate revenue delta between current and new scenarios.

    Args:
        df_with_revenue (pd.DataFrame): DataFrame with Current_Revenue and New_Revenue

    Returns:
        pd.DataFrame: DataFrame with delta columns added
    """
    df_delta = df_with_revenue.copy()

    # Calculate absolute delta
    df_delta['Revenue_Delta'] = df_delta['New_Revenue'] - df_delta['Current_Revenue']

    # Calculate percentage delta
    df_delta['Revenue_Delta_Pct'] = (
        df_delta['Revenue_Delta'] / df_delta['Current_Revenue']
    ) * 100

    return df_delta

def get_tier_summary(df):
    """
    Get summary statistics by tier.

    Args:
        df (pd.DataFrame): DataFrame with tier assignments and revenue

    Returns:
        pd.DataFrame: Summary by tier
    """
    summary = df.groupby('Tier').agg({
        'Brand Name': 'count',
        'Current_Revenue': 'sum',
        'New_Revenue': 'sum',
        'Marketplace Fee': 'mean',
        'New_Fee': 'mean',
        'Annualized Trips': 'sum',
        'New_Trips': 'sum'
    }).round(2)

    summary = summary.rename(columns={'Brand Name': 'Brand_Count'})

    # Calculate deltas
    summary['Revenue_Delta'] = summary['New_Revenue'] - summary['Current_Revenue']
    summary['Revenue_Delta_Pct'] = (
        (summary['New_Revenue'] - summary['Current_Revenue']) / summary['Current_Revenue']
    ) * 100

    # Reorder tiers
    tier_order = ['S-tier', 'A-tier', 'B-tier', 'C-tier']
    summary = summary.reindex([t for t in tier_order if t in summary.index])

    return summary

def calculate_baseline_economics(df, delivery_fee=2.50, courier_cost=5.00,
                                defect_rate=0.07, avg_refund=15.00, platform_costs=10e6):
    """
    Calculate baseline unit economics and P&L.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        delivery_fee (float): Current delivery fee per order
        courier_cost (float): Courier cost per delivery
        defect_rate (float): Current defect rate
        avg_refund (float): Average refund per defect
        platform_costs (float): Annual platform costs

    Returns:
        dict: Baseline economics
    """
    total_orders = df['Annualized Trips'].sum()
    avg_basket = (df['Annualized Trips'] * df['Avg. Basket Size']).sum() / total_orders

    # Revenue
    marketplace_revenue = (df['Annualized Trips'] * df['Avg. Basket Size'] * df['Marketplace Fee']).sum()
    delivery_revenue = total_orders * delivery_fee
    total_revenue = marketplace_revenue + delivery_revenue

    # Costs
    courier_costs = total_orders * courier_cost
    refund_costs = total_orders * defect_rate * avg_refund
    total_costs = courier_costs + refund_costs + platform_costs

    # Margin
    contribution_margin = total_revenue - total_costs
    margin_pct = (contribution_margin / total_revenue) * 100 if total_revenue > 0 else 0

    return {
        'total_orders': total_orders,
        'avg_basket': avg_basket,
        'marketplace_revenue': marketplace_revenue,
        'delivery_revenue': delivery_revenue,
        'total_revenue': total_revenue,
        'courier_costs': courier_costs,
        'refund_costs': refund_costs,
        'platform_costs': platform_costs,
        'total_costs': total_costs,
        'contribution_margin': contribution_margin,
        'margin_pct': margin_pct,
        'delivery_fee': delivery_fee,
        'courier_cost': courier_cost,
        'defect_rate': defect_rate,
        'avg_refund': avg_refund
    }

def calculate_delivery_fee_scenario(baseline, delivery_fee_increase):
    """
    Calculate impact of delivery fee optimization.

    Args:
        baseline (dict): Baseline economics
        delivery_fee_increase (float): Increase in delivery fee (e.g., 1.50 for $1.50)

    Returns:
        dict: New economics with delivery fee increase
    """
    new_delivery_fee = baseline['delivery_fee'] + delivery_fee_increase
    new_delivery_revenue = baseline['total_orders'] * new_delivery_fee

    new_total_revenue = baseline['marketplace_revenue'] + new_delivery_revenue
    new_contribution_margin = new_total_revenue - baseline['total_costs']
    new_margin_pct = (new_contribution_margin / new_total_revenue) * 100 if new_total_revenue > 0 else 0

    return {
        **baseline,
        'delivery_fee': new_delivery_fee,
        'delivery_revenue': new_delivery_revenue,
        'total_revenue': new_total_revenue,
        'contribution_margin': new_contribution_margin,
        'margin_pct': new_margin_pct,
        'delta': new_contribution_margin - baseline['contribution_margin']
    }

def calculate_defect_reduction_scenario(baseline, defect_reduction_pct):
    """
    Calculate impact of defect rate reduction.

    Args:
        baseline (dict): Baseline economics
        defect_reduction_pct (float): Reduction percentage (e.g., 0.50 for 50% reduction)

    Returns:
        dict: New economics with reduced defects
    """
    new_defect_rate = baseline['defect_rate'] * (1 - defect_reduction_pct)
    new_refund_costs = baseline['total_orders'] * new_defect_rate * baseline['avg_refund']

    new_total_costs = baseline['courier_costs'] + new_refund_costs + baseline['platform_costs']
    new_contribution_margin = baseline['total_revenue'] - new_total_costs
    new_margin_pct = (new_contribution_margin / baseline['total_revenue']) * 100 if baseline['total_revenue'] > 0 else 0

    return {
        **baseline,
        'defect_rate': new_defect_rate,
        'refund_costs': new_refund_costs,
        'total_costs': new_total_costs,
        'contribution_margin': new_contribution_margin,
        'margin_pct': new_margin_pct,
        'delta': new_contribution_margin - baseline['contribution_margin']
    }

def calculate_courier_efficiency_scenario(baseline, efficiency_gain_pct):
    """
    Calculate impact of courier efficiency improvements.

    Args:
        baseline (dict): Baseline economics
        efficiency_gain_pct (float): Efficiency gain (e.g., 0.15 for 15% more deliveries)

    Returns:
        dict: New economics with courier efficiency
    """
    # Same courier cost, but can handle more orders
    new_total_orders = baseline['total_orders'] * (1 + efficiency_gain_pct)

    # Revenue scales with orders
    new_marketplace_revenue = baseline['marketplace_revenue'] * (1 + efficiency_gain_pct)
    new_delivery_revenue = baseline['delivery_revenue'] * (1 + efficiency_gain_pct)
    new_total_revenue = new_marketplace_revenue + new_delivery_revenue

    # Costs scale proportionally
    new_courier_costs = baseline['courier_costs'] * (1 + efficiency_gain_pct)
    new_refund_costs = baseline['refund_costs'] * (1 + efficiency_gain_pct)
    new_total_costs = new_courier_costs + new_refund_costs + baseline['platform_costs']

    new_contribution_margin = new_total_revenue - new_total_costs
    new_margin_pct = (new_contribution_margin / new_total_revenue) * 100 if new_total_revenue > 0 else 0

    return {
        **baseline,
        'total_orders': new_total_orders,
        'marketplace_revenue': new_marketplace_revenue,
        'delivery_revenue': new_delivery_revenue,
        'total_revenue': new_total_revenue,
        'courier_costs': new_courier_costs,
        'refund_costs': new_refund_costs,
        'total_costs': new_total_costs,
        'contribution_margin': new_contribution_margin,
        'margin_pct': new_margin_pct,
        'delta': new_contribution_margin - baseline['contribution_margin']
    }

def calculate_combined_scenario(baseline, delivery_fee_increase, defect_reduction_pct, efficiency_gain_pct):
    """
    Calculate combined impact of all improvements.

    Args:
        baseline (dict): Baseline economics
        delivery_fee_increase (float): Delivery fee increase
        defect_reduction_pct (float): Defect reduction percentage
        efficiency_gain_pct (float): Efficiency gain percentage

    Returns:
        dict: Combined economics
    """
    # Apply all improvements together
    new_total_orders = baseline['total_orders'] * (1 + efficiency_gain_pct)
    new_delivery_fee = baseline['delivery_fee'] + delivery_fee_increase
    new_defect_rate = baseline['defect_rate'] * (1 - defect_reduction_pct)

    # Revenue
    new_marketplace_revenue = baseline['marketplace_revenue'] * (1 + efficiency_gain_pct)
    new_delivery_revenue = new_total_orders * new_delivery_fee
    new_total_revenue = new_marketplace_revenue + new_delivery_revenue

    # Costs
    new_courier_costs = baseline['courier_costs'] * (1 + efficiency_gain_pct)
    new_refund_costs = new_total_orders * new_defect_rate * baseline['avg_refund']
    new_total_costs = new_courier_costs + new_refund_costs + baseline['platform_costs']

    # Margin
    new_contribution_margin = new_total_revenue - new_total_costs
    new_margin_pct = (new_contribution_margin / new_total_revenue) * 100 if new_total_revenue > 0 else 0

    return {
        **baseline,
        'total_orders': new_total_orders,
        'delivery_fee': new_delivery_fee,
        'defect_rate': new_defect_rate,
        'marketplace_revenue': new_marketplace_revenue,
        'delivery_revenue': new_delivery_revenue,
        'total_revenue': new_total_revenue,
        'courier_costs': new_courier_costs,
        'refund_costs': new_refund_costs,
        'total_costs': new_total_costs,
        'contribution_margin': new_contribution_margin,
        'margin_pct': new_margin_pct,
        'delta': new_contribution_margin - baseline['contribution_margin']
    }

def calculate_revenue_per_brand(df):
    """
    Calculate revenue metrics per brand.

    Args:
        df (pd.DataFrame): Restaurant brands dataset

    Returns:
        pd.DataFrame: DataFrame with added revenue columns
    """
    df_calc = df.copy()

    # Calculate annual revenue from marketplace fees
    df_calc['Annual_Revenue'] = (
        df_calc['Annualized Trips'] *
        df_calc['Avg. Basket Size'] *
        df_calc['Marketplace Fee']
    )

    # Calculate revenue per location
    df_calc['Revenue_Per_Active_Location'] = (
        df_calc['Annual_Revenue'] / df_calc['Active Locations']
    )

    # Calculate revenue per trip
    df_calc['Revenue_Per_Trip'] = (
        df_calc['Avg. Basket Size'] * df_calc['Marketplace Fee']
    )

    return df_calc

def optimize_marketplace_fee(df, target_revenue_change=0.0):
    """
    Analyze marketplace fee optimization opportunities.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        target_revenue_change (float): Target revenue change percentage (e.g., 0.05 for 5% increase)

    Returns:
        pd.DataFrame: DataFrame with fee optimization recommendations
    """
    df_opt = calculate_revenue_per_brand(df)

    # Price elasticity assumptions (can be customized based on business knowledge)
    # Assume -1.5 elasticity (1% fee increase leads to 1.5% trip decrease)
    elasticity = -1.5

    # Calculate optimal fee adjustments
    df_opt['Current_Fee_Pct'] = df_opt['Marketplace Fee'] * 100

    # Simulate fee changes from -5% to +5% in 0.5% increments
    fee_changes = np.arange(-0.05, 0.06, 0.005)

    # For each brand, find the fee change that maximizes revenue
    optimal_fees = []
    for idx, row in df_opt.iterrows():
        current_revenue = row['Annual_Revenue']
        current_fee = row['Marketplace Fee']
        current_trips = row['Annualized Trips']

        max_revenue = current_revenue
        optimal_fee = current_fee
        optimal_trips = current_trips

        for fee_change in fee_changes:
            new_fee = current_fee * (1 + fee_change)
            # Estimate trip change based on elasticity
            trip_change = fee_change * elasticity
            new_trips = current_trips * (1 + trip_change)
            new_revenue = new_trips * row['Avg. Basket Size'] * new_fee

            if new_revenue > max_revenue:
                max_revenue = new_revenue
                optimal_fee = new_fee
                optimal_trips = new_trips

        optimal_fees.append({
            'Optimal_Fee': optimal_fee,
            'Optimal_Fee_Pct': optimal_fee * 100,
            'Fee_Change_Pct': ((optimal_fee - current_fee) / current_fee) * 100,
            'Projected_Trips': optimal_trips,
            'Projected_Revenue': max_revenue,
            'Revenue_Change': max_revenue - current_revenue,
            'Revenue_Change_Pct': ((max_revenue - current_revenue) / current_revenue) * 100
        })

    # Add optimal fee columns to dataframe
    optimal_df = pd.DataFrame(optimal_fees)
    df_opt = pd.concat([df_opt, optimal_df], axis=1)

    return df_opt

def calculate_unit_economics(df, cost_assumptions=None):
    """
    Calculate unit economics metrics.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        cost_assumptions (dict): Cost structure assumptions

    Returns:
        pd.DataFrame: DataFrame with unit economics calculations
    """
    # Default cost assumptions (can be customized)
    if cost_assumptions is None:
        cost_assumptions = {
            'courier_cost_per_trip': 5.0,  # Average courier payout
            'customer_acquisition_cost': 15.0,  # CAC for first-time customers
            'processing_fee': 0.30,  # Per-transaction processing fee
            'support_cost_per_defect': 10.0  # Cost to handle defects
        }

    df_econ = calculate_revenue_per_brand(df)

    # Calculate costs per trip
    df_econ['Courier_Cost_Per_Trip'] = cost_assumptions['courier_cost_per_trip']
    df_econ['Processing_Cost_Per_Trip'] = cost_assumptions['processing_fee']

    # Calculate defect costs
    df_econ['Defect_Cost_Per_Trip'] = (
        df_econ['Order Defect Rate'] * cost_assumptions['support_cost_per_defect']
    )

    # Calculate acquisition costs (amortized across all trips)
    df_econ['Acquisition_Cost_Per_Trip'] = (
        df_econ['%Orders from First Time Eaters'] *
        cost_assumptions['customer_acquisition_cost']
    )

    # Total cost per trip
    df_econ['Total_Cost_Per_Trip'] = (
        df_econ['Courier_Cost_Per_Trip'] +
        df_econ['Processing_Cost_Per_Trip'] +
        df_econ['Defect_Cost_Per_Trip'] +
        df_econ['Acquisition_Cost_Per_Trip']
    )

    # Contribution margin per trip
    df_econ['Contribution_Margin_Per_Trip'] = (
        df_econ['Revenue_Per_Trip'] - df_econ['Total_Cost_Per_Trip']
    )

    # Contribution margin percentage
    df_econ['Contribution_Margin_Pct'] = (
        (df_econ['Contribution_Margin_Per_Trip'] / df_econ['Revenue_Per_Trip']) * 100
    )

    # Annual contribution margin
    df_econ['Annual_Contribution_Margin'] = (
        df_econ['Contribution_Margin_Per_Trip'] * df_econ['Annualized Trips']
    )

    # Flag unprofitable brands
    df_econ['Is_Profitable'] = df_econ['Contribution_Margin_Per_Trip'] > 0

    return df_econ

def simulate_growth_scenarios(df, growth_assumptions):
    """
    Simulate different growth scenarios.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        growth_assumptions (dict): Growth scenario parameters

    Returns:
        pd.DataFrame: Projected metrics under different scenarios
    """
    df_growth = calculate_unit_economics(df)

    # Apply growth assumptions
    trip_growth = growth_assumptions.get('trip_growth', 0.20)  # 20% default
    location_growth = growth_assumptions.get('location_growth', 0.15)  # 15% default
    basket_growth = growth_assumptions.get('basket_growth', 0.05)  # 5% default

    # Project future metrics
    df_growth['Projected_Trips'] = df_growth['Annualized Trips'] * (1 + trip_growth)
    df_growth['Projected_Locations'] = df_growth['Active Locations'] * (1 + location_growth)
    df_growth['Projected_Basket_Size'] = df_growth['Avg. Basket Size'] * (1 + basket_growth)

    # Recalculate revenue with growth
    df_growth['Projected_Revenue'] = (
        df_growth['Projected_Trips'] *
        df_growth['Projected_Basket_Size'] *
        df_growth['Marketplace Fee']
    )

    # Calculate revenue uplift
    df_growth['Revenue_Uplift'] = (
        df_growth['Projected_Revenue'] - df_growth['Annual_Revenue']
    )

    df_growth['Revenue_Uplift_Pct'] = (
        (df_growth['Revenue_Uplift'] / df_growth['Annual_Revenue']) * 100
    )

    return df_growth

def calculate_customer_ltv(df, retention_assumptions=None):
    """
    Calculate Customer Lifetime Value (LTV) by cohort and segment.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        retention_assumptions (dict): Monthly retention curve assumptions

    Returns:
        pd.DataFrame: DataFrame with LTV metrics
    """
    # Default retention curve (industry benchmarks for food delivery)
    if retention_assumptions is None:
        retention_assumptions = {
            'month_1': 0.65,   # 65% order again in Month 1
            'month_3': 0.45,   # 45% still active at Month 3
            'month_6': 0.35,   # 35% still active at Month 6
            'month_12': 0.20,  # 20% make it to Year 2
            'month_24': 0.10   # 10% two-year customers
        }

    df_ltv = df.copy()

    # Calculate average orders per active month
    avg_orders_per_month = 2.5  # Industry benchmark

    # Calculate monthly contribution margin per customer
    monthly_contribution = (
        avg_orders_per_month *
        df_ltv['Avg. Basket Size'] *
        df_ltv['Marketplace Fee']
    )

    # Calculate 12-month LTV using retention curve
    # LTV = Sum of (monthly_contribution * retention_rate) for each month
    ltv_12_month = (
        monthly_contribution * (
            retention_assumptions['month_1'] +
            retention_assumptions['month_3'] * 2 +  # Months 2-3
            retention_assumptions['month_6'] * 3 +  # Months 4-6
            retention_assumptions['month_12'] * 6   # Months 7-12
        )
    )

    df_ltv['LTV_12_Month'] = ltv_12_month.round(2)

    # Calculate Customer Acquisition Cost (CAC)
    # Assume acquisition cost is concentrated in first-time orders
    df_ltv['CAC'] = df_ltv['%Orders from First Time Eaters'] * 15.0  # $15 CAC per first-time customer

    # Calculate CAC Payback Period (months)
    df_ltv['CAC_Payback_Months'] = (
        df_ltv['CAC'] / monthly_contribution
    ).round(1)

    # Calculate LTV:CAC Ratio (target: > 3.0)
    df_ltv['LTV_CAC_Ratio'] = (
        df_ltv['LTV_12_Month'] / df_ltv['CAC']
    ).round(2)

    # Flag healthy unit economics
    df_ltv['Healthy_LTV'] = df_ltv['LTV_CAC_Ratio'] > 3.0

    # Calculate lifetime margin
    df_ltv['Lifetime_Margin'] = (
        df_ltv['LTV_12_Month'] - df_ltv['CAC']
    ).round(2)

    return df_ltv

def analyze_density_effects(df):
    """
    Analyze correlation between location density and performance metrics.

    Args:
        df (pd.DataFrame): Restaurant brands dataset

    Returns:
        dict: Correlation analysis results
    """
    df_density = df.copy()

    # Calculate locations per active location (density proxy)
    # Higher ratio = more concentrated/dense markets
    df_density['Location_Density_Score'] = (
        df_density['Active Locations'] / df_density['Active Locations'].mean()
    )

    # Calculate correlations
    correlations = {
        'Density_vs_Basket_Size': df_density[['Location_Density_Score', 'Avg. Basket Size']].corr().iloc[0, 1],
        'Density_vs_Defect_Rate': df_density[['Location_Density_Score', 'Order Defect Rate']].corr().iloc[0, 1],
        'Density_vs_Wait_Time': df_density[['Location_Density_Score', 'Avg. Courier Wait Time (min)']].corr().iloc[0, 1],
        'Density_vs_FTO_Rate': df_density[['Location_Density_Score', '%Orders from First Time Eaters']].corr().iloc[0, 1]
    }

    # Create density tiers
    df_density['Density_Tier'] = pd.qcut(
        df_density['Location_Density_Score'],
        q=4,
        labels=['Low Density', 'Medium-Low', 'Medium-High', 'High Density']
    )

    # Aggregate metrics by density tier
    density_summary = df_density.groupby('Density_Tier').agg({
        'Avg. Basket Size': 'mean',
        'Order Defect Rate': 'mean',
        'Avg. Courier Wait Time (min)': 'mean',
        '%Orders from First Time Eaters': 'mean',
        'Annualized Trips': 'sum',
        'Brand Name': 'count'
    }).round(2)

    return {
        'correlations': correlations,
        'density_summary': density_summary,
        'density_dataframe': df_density
    }

def calculate_restaurant_profitability(df):
    """
    Estimate restaurant-side P&L on Uber Eats platform.

    IMPORTANT: This helps identify at-risk merchants who may churn.

    Args:
        df (pd.DataFrame): Restaurant brands dataset

    Returns:
        pd.DataFrame: DataFrame with restaurant profitability estimates
    """
    df_restaurant = df.copy()

    # Revenue from Uber Eats (per order)
    avg_order_value = df_restaurant['Avg. Basket Size']

    # Uber Eats takes marketplace fee
    marketplace_fee_amount = avg_order_value * df_restaurant['Marketplace Fee']

    # Restaurant receives
    restaurant_revenue_per_order = avg_order_value - marketplace_fee_amount

    # Restaurant costs (estimates)
    cogs_rate = 0.30  # 30% Cost of Goods Sold
    labor_per_order = 5.00  # $5 labor cost per order
    packaging_cost = 1.50  # $1.50 packaging/delivery prep

    restaurant_cogs = avg_order_value * cogs_rate
    total_restaurant_costs = restaurant_cogs + labor_per_order + packaging_cost

    # Restaurant margin per order
    restaurant_margin = restaurant_revenue_per_order - total_restaurant_costs

    # Annual restaurant profit from Uber Eats
    restaurant_annual_profit = restaurant_margin * df_restaurant['Annualized Trips']

    # Add to dataframe
    df_restaurant['Restaurant_Revenue_Per_Order'] = restaurant_revenue_per_order.round(2)
    df_restaurant['Restaurant_Margin_Per_Order'] = restaurant_margin.round(2)
    df_restaurant['Restaurant_Annual_Profit'] = restaurant_annual_profit.round(0)

    # Calculate restaurant margin %
    df_restaurant['Restaurant_Margin_Pct'] = (
        (restaurant_margin / avg_order_value) * 100
    ).round(1)

    # Flag at-risk merchants (negative margin or < 5% margin)
    df_restaurant['At_Risk'] = (restaurant_margin < 0) | (df_restaurant['Restaurant_Margin_Pct'] < 5)

    # Calculate how much fee reduction would bring them to 10% margin
    target_margin_pct = 0.10  # 10% target
    current_revenue_to_restaurant = avg_order_value * (1 - df_restaurant['Marketplace Fee'])
    target_revenue_to_restaurant = avg_order_value * (1 - target_margin_pct) - total_restaurant_costs

    required_fee_reduction = (target_revenue_to_restaurant - current_revenue_to_restaurant) / avg_order_value
    df_restaurant['Fee_Reduction_To_10pct_Margin'] = required_fee_reduction.clip(lower=0).round(3)

    return df_restaurant

def calculate_cohort_retention(df, cohort_months=12):
    """
    Model customer retention by cohort over time.

    Args:
        df (pd.DataFrame): Restaurant brands dataset
        cohort_months (int): Number of months to model

    Returns:
        pd.DataFrame: Retention curve by merchant
    """
    df_cohort = df.copy()

    # Model retention curve (exponential decay)
    # Monthly retention rate varies by merchant quality
    base_retention = 0.80  # 80% base monthly retention

    # Quality merchants have higher retention
    quality_bonus = (
        (1 - df_cohort['Order Defect Rate']) * 0.10  # Lower defects = +10% retention
    )

    monthly_retention_rate = (base_retention + quality_bonus).clip(upper=0.95)

    df_cohort['Monthly_Retention_Rate'] = monthly_retention_rate.round(3)

    # Calculate retention at Month 3, 6, 12
    df_cohort['Retention_Month_3'] = (monthly_retention_rate ** 3).round(3)
    df_cohort['Retention_Month_6'] = (monthly_retention_rate ** 6).round(3)
    df_cohort['Retention_Month_12'] = (monthly_retention_rate ** 12).round(3)

    # Calculate expected customer lifetime (in months)
    # Lifetime = 1 / (1 - retention_rate)
    df_cohort['Expected_Lifetime_Months'] = (
        1 / (1 - monthly_retention_rate)
    ).round(1)

    return df_cohort
