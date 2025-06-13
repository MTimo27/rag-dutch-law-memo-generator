import json
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pathlib import Path
from scipy import stats
import pandas as pd

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

SUMMARY_DIR = "./results/claude_temperature/eval_summaries"
PLOT_OUTPUT_DIR = "./results/claude_temperature/plots_across_temperatures"
Path(PLOT_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

TARGET_METRICS = ["citation_precision", "citation_recall", "f1_score", "hallucinated", "ungrounded_ratio", "fabricated_eclis"]

# Metric categories for better organization
PERFORMANCE_METRICS = ["citation_precision", "citation_recall", "f1_score"]
ERROR_METRICS = ["hallucinated", "ungrounded_ratio", "fabricated_eclis"]

summary_files = glob.glob(f"{SUMMARY_DIR}/results_summary_*.json")
if not summary_files:
    raise FileNotFoundError(f"No summary files found in {SUMMARY_DIR}")

data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
temperature_counts = defaultdict(int)

for path in summary_files:
    temp_str = path.split("_")[-1].replace(".json", "")
    try:
        temperature = float(temp_str)
        temperature_counts[temperature] += 1
    except ValueError:
        print(f"Warning: Could not parse temperature from {path}")
        continue
        
    with open(path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    for result in summary["results"]:
        metric_name = result["similarity_metric"]
        threshold = result["threshold"]

        for m in TARGET_METRICS:
            if m in result:
                val = result[m]
                if not np.isnan(val):  
                    data[m][(metric_name, threshold)][temperature].append(val)

print(f"Loaded data for temperatures: {sorted(temperature_counts.keys())}")
print(f"Sample counts per temperature: {dict(temperature_counts)}")

def create_metric_comparison_plot():
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Temperature Impact on Model Performance Metrics', fontsize=16, fontweight='bold')
    
    for idx, metric in enumerate(TARGET_METRICS):
        ax = axes[idx // 3, idx % 3]
        
        # Collect all data points for this metric
        all_temps = set()
        metric_data = []
        
        for (similarity_metric, threshold), temp_dict in data[metric].items():
            all_temps.update(temp_dict.keys())
            
        temps = sorted(all_temps)
        
        # Plot each similarity metric/threshold combination
        for (similarity_metric, threshold), temp_dict in data[metric].items():
            temp_values = []
            metric_means = []
            metric_stds = []
            
            for temp in temps:
                if temp in temp_dict and len(temp_dict[temp]) > 0:
                    values = temp_dict[temp]
                    temp_values.append(temp)
                    metric_means.append(np.mean(values))
                    metric_stds.append(np.std(values))
            
            if temp_values:
                label = f"{similarity_metric}@{threshold}"
                ax.errorbar(temp_values, metric_means, yerr=metric_stds, 
                           label=label, marker='o', capsize=3, alpha=0.8)
        
        ax.set_title(f"{metric.replace('_', ' ').title()}", fontweight='bold')
        ax.set_xlabel("Temperature")
        ax.set_ylabel("Score")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc='best')
        
       
        if metric in ERROR_METRICS:
            ax.set_facecolor('#fff2f2')  
        else:
            ax.set_facecolor('#f2fff2')  
    
    plt.tight_layout()
    plt.savefig(f"{PLOT_OUTPUT_DIR}/comprehensive_metrics_dashboard.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: comprehensive_metrics_dashboard.png")

def create_tradeoff_analysis():
    temps = sorted(set().union(*[temp_dict.keys() for metric_data in data.values() 
                                for temp_dict in metric_data.values()]))
    
    perf_scores = []
    error_scores = []
    temp_labels = []
    
    for temp in temps:
        perf_vals = []
        error_vals = []
        
        for metric in PERFORMANCE_METRICS:
            for temp_dict in data[metric].values():
                if temp in temp_dict:
                    perf_vals.extend(temp_dict[temp])
        
        for metric in ERROR_METRICS:
            for temp_dict in data[metric].values():
                if temp in temp_dict:
                    error_vals.extend(temp_dict[temp])
        
        if perf_vals and error_vals:
            perf_scores.append(np.mean(perf_vals))
            error_scores.append(np.mean(error_vals))
            temp_labels.append(temp)
    
    # Create scatter plot with temperature progression
    fig, ax = plt.subplots(figsize=(10, 8))
    scatter = ax.scatter(error_scores, perf_scores, c=temp_labels, cmap='coolwarm', 
                        s=100, alpha=0.7, edgecolors='black')
    
    # Add temperature labels
    for i, temp in enumerate(temp_labels):
        ax.annotate(f'T={temp}', (error_scores[i], perf_scores[i]), 
                   xytext=(5, 5), textcoords='offset points', fontsize=9)
    
    # Add trend line
    z = np.polyfit(error_scores, perf_scores, 1)
    p = np.poly1d(z)
    ax.plot(error_scores, p(error_scores), "r--", alpha=0.8, 
            label=f'Trend: R²={stats.pearsonr(error_scores, perf_scores)[0]**2:.3f}')
    
    ax.set_xlabel('Average Error Score', fontsize=12)
    ax.set_ylabel('Average Performance Score', fontsize=12)
    ax.set_title('Performance vs Error Trade-off Across Temperatures', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Add colorbar
    cbar = plt.colorbar(scatter)
    cbar.set_label('Temperature', rotation=270, labelpad=15)
    
    plt.tight_layout()
    plt.savefig(f"{PLOT_OUTPUT_DIR}/performance_error_tradeoff.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: performance_error_tradeoff.png")

def analyze_statistical_significance():
    results = {}
    
    for metric in TARGET_METRICS:
        # Collect all temperature groups for this metric
        temp_groups = defaultdict(list)
        for temp_dict in data[metric].values():
            for temp, values in temp_dict.items():
                temp_groups[temp].extend(values)
        
        temps = sorted(temp_groups.keys())
        if len(temps) < 2:
            continue
            
        # Filter groups with sufficient data and variance
        valid_groups = []
        valid_temps = []
        temp_means = {}
        
        for temp in temps:
            group = temp_groups[temp]
            if len(group) >= 2:  # Need at least 2 samples
                group_std = np.std(group, ddof=1)
                group_mean = np.mean(group)
                temp_means[temp] = group_mean
                
                # Only include if there's some variance or if we have multiple groups with different means
                if group_std > 1e-10 or len(set([np.mean(temp_groups[t]) for t in temps])) > 1:
                    valid_groups.append(group)
                    valid_temps.append(temp)
            elif len(group) == 1:
                temp_means[temp] = group[0]
        
        # Perform statistical tests only if we have valid data
        if len(valid_groups) >= 2:
            try:
                # Pre-check for constant inputs to avoid scipy warnings
                all_values = np.concatenate(valid_groups)
                overall_variance = np.var(all_values, ddof=1) if len(all_values) > 1 else 0
                
                # Check if each group is constant
                group_variances = [np.var(group, ddof=1) if len(group) > 1 else 0 for group in valid_groups]
                all_groups_constant = all(var < 1e-10 for var in group_variances)
                
                if overall_variance < 1e-10:
                    # All values are essentially identical across all groups
                    results[metric] = {
                        'f_statistic': 0.0,
                        'p_value': 1.0,
                        'significant': False,
                        'temperature_means': temp_means,
                        'test_status': 'constant_values'
                    }
                elif all_groups_constant:
                    # Each group is constant but groups have different means
                    # This represents perfect separation
                    results[metric] = {
                        'f_statistic': np.inf,
                        'p_value': 0.0,
                        'significant': True,
                        'temperature_means': temp_means,
                        'test_status': 'perfect_separation'
                    }
                else:
                    # Suppress scipy warnings for this specific computation
                    import warnings
                    with warnings.catch_warnings():
                        warnings.filterwarnings('ignore', category=RuntimeWarning)
                        warnings.filterwarnings('ignore', message='Each of the input arrays is constant')
                        
                        f_stat, p_value = stats.f_oneway(*valid_groups)
                    
                    # Handle edge cases in results
                    if np.isinf(f_stat):
                        test_status = 'perfect_separation'
                        p_value = 0.0
                    elif np.isnan(f_stat) or np.isnan(p_value):
                        f_stat = np.nan
                        p_value = np.nan
                        test_status = 'invalid_computation'
                    else:
                        test_status = 'valid'
                    
                    results[metric] = {
                        'f_statistic': f_stat,
                        'p_value': p_value,
                        'significant': p_value < 0.05 if not np.isnan(p_value) else False,
                        'temperature_means': temp_means,
                        'test_status': test_status
                    }
            except Exception as e:
                print(f"Warning: Statistical test failed for {metric}: {e}")
                results[metric] = {
                    'f_statistic': np.nan,
                    'p_value': np.nan,
                    'significant': False,
                    'temperature_means': temp_means,
                    'test_status': 'test_failed'
                }
        else:
            # Insufficient data for statistical testing
            results[metric] = {
                'f_statistic': np.nan,
                'p_value': np.nan,
                'significant': False,
                'temperature_means': temp_means,
                'test_status': 'insufficient_data'
            }
    
    # Create significance summary plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Filter metrics with valid results
    valid_metrics = [(m, r) for m, r in results.items() 
                    if r['test_status'] in ['valid', 'perfect_separation', 'constant_values']]
    
    if valid_metrics:
        metrics_with_results = [m for m, r in valid_metrics]
        metric_results = [r for m, r in valid_metrics]
        
        # Plot 1: P-values (handle special cases)
        p_values = []
        colors = []
        for result in metric_results:
            p_val = result['p_value']
            if result['test_status'] == 'constant_values':
                p_values.append(1.0)
                colors.append('gray')
            elif result['test_status'] == 'perfect_separation':
                p_values.append(0.001)  # Display value for infinite F
                colors.append('darkred')
            elif not np.isnan(p_val):
                p_values.append(max(p_val, 1e-10))  # Avoid log(0)
                colors.append('red' if p_val < 0.05 else 'blue')
            else:
                p_values.append(0.1)  # Default for invalid cases
                colors.append('gray')
        
        ax1.barh(range(len(metrics_with_results)), p_values, color=colors, alpha=0.7)
        ax1.axvline(x=0.05, color='red', linestyle='--', label='α = 0.05')
        ax1.set_yticks(range(len(metrics_with_results)))
        ax1.set_yticklabels([m.replace('_', ' ').title() for m in metrics_with_results])
        ax1.set_xlabel('P-value')
        ax1.set_title('Statistical Significance of Temperature Effects')
        ax1.legend()
        ax1.set_xscale('log')
        
        # Add status annotations
        for i, result in enumerate(metric_results):
            status = result['test_status']
            if status != 'valid':
                ax1.text(max(p_values) * 1.1, i, status.replace('_', ' '), 
                        fontsize=8, va='center')
        
        # Plot 2: Effect sizes (coefficient of variation across temperatures)
        effect_sizes = []
        for result in metric_results:
            temp_means = list(result['temperature_means'].values())
            if len(temp_means) > 1 and np.mean(temp_means) != 0:
                cv = np.std(temp_means, ddof=1) / np.abs(np.mean(temp_means))
                effect_sizes.append(cv)
            else:
                effect_sizes.append(0)
        
        ax2.barh(range(len(metrics_with_results)), effect_sizes, alpha=0.7)
        ax2.set_yticks(range(len(metrics_with_results)))
        ax2.set_yticklabels([m.replace('_', ' ').title() for m in metrics_with_results])
        ax2.set_xlabel('Coefficient of Variation')
        ax2.set_title('Effect Size of Temperature on Metrics')
    else:
        ax1.text(0.5, 0.5, 'No valid statistical tests performed', 
                ha='center', va='center', transform=ax1.transAxes)
        ax2.text(0.5, 0.5, 'Insufficient data for effect size analysis', 
                ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    plt.savefig(f"{PLOT_OUTPUT_DIR}/statistical_significance_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: statistical_significance_analysis.png")
    
    return results

def create_enhanced_ungrounded_analysis():
    all_temps = set()
    for _, temp_dict in data["ungrounded_ratio"].items():
        all_temps.update(temp_dict.keys())
    
    temps = sorted(all_temps)
    avg_vals = []
    ci_lower = []
    ci_upper = []
    sample_sizes = []
    
    for temp in temps:
        values = []
        for (_, _), temp_dict in data["ungrounded_ratio"].items():
            if temp in temp_dict:
                values.extend(temp_dict[temp])
        
        if values:
            mean_val = np.mean(values)
            sem = stats.sem(values)
            ci = stats.t.interval(0.95, len(values)-1, loc=mean_val, scale=sem)
            
            avg_vals.append(mean_val)
            ci_lower.append(ci[0])
            ci_upper.append(ci[1])
            sample_sizes.append(len(values))
        else:
            avg_vals.append(np.nan)
            ci_lower.append(np.nan)
            ci_upper.append(np.nan)
            sample_sizes.append(0)
    
    # Create enhanced plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Main trend plot with confidence intervals
    ax1.plot(temps, avg_vals, 'o-', color='darkred', linewidth=3, markersize=8, label='Mean Ungrounded Ratio')
    ax1.fill_between(temps, ci_lower, ci_upper, alpha=0.3, color='darkred', label='95% Confidence Interval')
    
    # Add trend line
    valid_mask = ~np.isnan(avg_vals)
    if np.sum(valid_mask) > 1:
        temps_valid = np.array(temps)[valid_mask]
        vals_valid = np.array(avg_vals)[valid_mask]
        z = np.polyfit(temps_valid, vals_valid, 1)
        p = np.poly1d(z)
        ax1.plot(temps_valid, p(temps_valid), "--", alpha=0.8, color='blue',
                label=f'Linear Trend (slope: {z[0]:.3f})')
    
    ax1.set_title('Ungrounded Ratio vs Temperature with Statistical Confidence', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Temperature')
    ax1.set_ylabel('Ungrounded Ratio')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1%}"))
    
    # Sample size plot
    ax2.bar(temps, sample_sizes, alpha=0.7, color='steelblue')
    ax2.set_title('Sample Sizes per Temperature', fontweight='bold')
    ax2.set_xlabel('Temperature')
    ax2.set_ylabel('Number of Samples')
    ax2.grid(True, alpha=0.3)
    
    # Add sample size annotations
    for temp, size in zip(temps, sample_sizes):
        if size > 0:
            ax2.text(temp, size + max(sample_sizes) * 0.01, str(size), 
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(f"{PLOT_OUTPUT_DIR}/enhanced_ungrounded_analysis.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: enhanced_ungrounded_analysis.png")

def main():
    print("Creating enhanced visualizations...")
    
    create_metric_comparison_plot()
    create_tradeoff_analysis()
    sig_results = analyze_statistical_significance()
    create_enhanced_ungrounded_analysis()
    
    # Print statistical summary
    for metric, result in sig_results.items():
        status = "SIGNIFICANT" if result['significant'] else "NOT SIGNIFICANT"
        test_status = result['test_status']
        f_stat = result['f_statistic']
        p_val = result['p_value']
        
        # Format F-statistic and p-value based on test status
        if test_status == 'constant_values':
            print(f"{metric}: {status} - All values identical across temperatures")
        elif test_status == 'perfect_separation':
            print(f"{metric}: {status} - Perfect group separation (F=∞, p≈0)")
        elif test_status == 'insufficient_data':
            print(f"{metric}: {status} - Insufficient data for testing")
        elif test_status == 'test_failed':
            print(f"{metric}: {status} - Statistical test failed")
        elif test_status == 'invalid_computation':
            print(f"{metric}: {status} - Invalid statistical computation")
        else:
            print(f"{metric}: {status} (p={p_val:.4f}, F={f_stat:.2f})")
    
    print(f"\nAll enhanced plots saved to: {PLOT_OUTPUT_DIR}")

if __name__ == "__main__":
    main()