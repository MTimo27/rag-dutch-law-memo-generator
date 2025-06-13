import json
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
from pathlib import Path
from scipy import stats
import pandas as pd
from matplotlib.patches import Rectangle

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

MODEL_1_DIR = "./results/gpt_temperature/eval_summaries"  # GPT-4.1 results
MODEL_2_DIR = "./results/claude_temperature/eval_summaries"  # Claude Sonnet 4 results
MODEL_1_NAME = "GPT-4.1"
MODEL_2_NAME = "Claude Sonnet 4"
COMPARISON_OUTPUT_DIR = "./results/model_comparison_plots"
Path(COMPARISON_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

TARGET_METRICS = ["citation_precision", "citation_recall", "f1_score", "hallucinated", "ungrounded_ratio", "fabricated_eclis"]
PERFORMANCE_METRICS = ["citation_precision", "citation_recall", "f1_score"]
ERROR_METRICS = ["hallucinated", "ungrounded_ratio", "fabricated_eclis"]

def load_model_data(summary_dir, model_name):
    summary_files = glob.glob(f"{summary_dir}/results_summary_*.json")
    if not summary_files:
        raise FileNotFoundError(f"No summary files found in {summary_dir}")
    
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
    
    print(f"Loaded {model_name} data for temperatures: {sorted(temperature_counts.keys())}")
    return data, temperature_counts

def create_side_by_side_comparison():
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle(f'{MODEL_1_NAME} vs {MODEL_2_NAME}: Temperature Impact Comparison', 
                 fontsize=16, fontweight='bold')
    
    for idx, metric in enumerate(TARGET_METRICS):
        ax = axes[idx // 3, idx % 3]
        
        # Get temperatures common to both models
        temps_model1 = set()
        temps_model2 = set()
        
        for temp_dict in data_model1[metric].values():
            temps_model1.update(temp_dict.keys())
        for temp_dict in data_model2[metric].values():
            temps_model2.update(temp_dict.keys())
            
        common_temps = sorted(temps_model1.intersection(temps_model2))
        
        if not common_temps:
            ax.text(0.5, 0.5, f'No overlapping temperatures\nfor {metric}', 
                   ha='center', va='center', transform=ax.transAxes)
            continue
        
        # Aggregate data across similarity metrics/thresholds for each model
        model1_means = []
        model1_stds = []
        model2_means = []
        model2_stds = []
        
        for temp in common_temps:
            # Model 1 aggregation
            temp_values_m1 = []
            for temp_dict in data_model1[metric].values():
                if temp in temp_dict:
                    temp_values_m1.extend(temp_dict[temp])
            
            # Model 2 aggregation  
            temp_values_m2 = []
            for temp_dict in data_model2[metric].values():
                if temp in temp_dict:
                    temp_values_m2.extend(temp_dict[temp])
            
            model1_means.append(np.mean(temp_values_m1) if temp_values_m1 else np.nan)
            model1_stds.append(np.std(temp_values_m1) if temp_values_m1 else np.nan)
            model2_means.append(np.mean(temp_values_m2) if temp_values_m2 else np.nan)
            model2_stds.append(np.std(temp_values_m2) if temp_values_m2 else np.nan)
        
        # Plot both models
        ax.errorbar(common_temps, model1_means, yerr=model1_stds, 
                   label=MODEL_1_NAME, marker='o', linewidth=2, markersize=6, capsize=4)
        ax.errorbar(common_temps, model2_means, yerr=model2_stds, 
                   label=MODEL_2_NAME, marker='s', linewidth=2, markersize=6, capsize=4)
        
        ax.set_title(f"{metric.replace('_', ' ').title()}", fontweight='bold', fontsize=12)
        ax.set_xlabel("Temperature")
        ax.set_ylabel("Score")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Color-code background
        if metric in ERROR_METRICS:
            ax.set_facecolor('#fff8f8')
        else:
            ax.set_facecolor('#f8fff8')
    
    plt.tight_layout()
    plt.savefig(f"{COMPARISON_OUTPUT_DIR}/side_by_side_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: side_by_side_comparison.png")

def create_difference_heatmap():
    common_temps = set()
    for metric in TARGET_METRICS:
        temps_m1 = set()
        temps_m2 = set()
        for temp_dict in data_model1[metric].values():
            temps_m1.update(temp_dict.keys())
        for temp_dict in data_model2[metric].values():
            temps_m2.update(temp_dict.keys())
        common_temps.update(temps_m1.intersection(temps_m2))
    
    common_temps = sorted(common_temps)
    
    # Create difference matrix
    diff_matrix = np.full((len(TARGET_METRICS), len(common_temps)), np.nan)
    
    for i, metric in enumerate(TARGET_METRICS):
        for j, temp in enumerate(common_temps):
            # Aggregate values for each model at this temperature
            vals_m1 = []
            vals_m2 = []
            
            for temp_dict in data_model1[metric].values():
                if temp in temp_dict:
                    vals_m1.extend(temp_dict[temp])
            
            for temp_dict in data_model2[metric].values():
                if temp in temp_dict:
                    vals_m2.extend(temp_dict[temp])
            
            if vals_m1 and vals_m2:
                mean_m1 = np.mean(vals_m1)
                mean_m2 = np.mean(vals_m2)
                diff_matrix[i, j] = mean_m2 - mean_m1  # Claude - GPT
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Handle NaN values for colormap
    masked_matrix = np.ma.masked_invalid(diff_matrix)
    
    im = ax.imshow(masked_matrix, cmap='RdBu_r', aspect='auto', vmin=-0.2, vmax=0.2)
    
    # Set ticks and labels
    ax.set_xticks(range(len(common_temps)))
    ax.set_xticklabels([f'{t:.2f}' for t in common_temps])
    ax.set_yticks(range(len(TARGET_METRICS)))
    ax.set_yticklabels([m.replace('_', ' ').title() for m in TARGET_METRICS])
    
    # Add text annotations
    for i in range(len(TARGET_METRICS)):
        for j in range(len(common_temps)):
            if not np.isnan(diff_matrix[i, j]):
                text_color = 'white' if abs(diff_matrix[i, j]) > 0.1 else 'black'
                ax.text(j, i, f'{diff_matrix[i, j]:.3f}', 
                       ha='center', va='center', color=text_color, fontweight='bold')
    
    ax.set_title(f'Performance Difference Heatmap\n({MODEL_2_NAME} - {MODEL_1_NAME})', 
                fontsize=14, fontweight='bold')
    ax.set_xlabel('Temperature')
    ax.set_ylabel('Metrics')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Performance Difference', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.savefig(f"{COMPARISON_OUTPUT_DIR}/difference_heatmap.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: difference_heatmap.png")

def create_statistical_comparison():
    comparison_results = {}
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    metrics_tested = []
    p_values = []
    effect_sizes = []
    better_model = []
    
    for metric in TARGET_METRICS:
        # Get common temperatures
        temps_m1 = set()
        temps_m2 = set()
        for temp_dict in data_model1[metric].values():
            temps_m1.update(temp_dict.keys())
        for temp_dict in data_model2[metric].values():
            temps_m2.update(temp_dict.keys())
        common_temps = temps_m1.intersection(temps_m2)
        
        if not common_temps:
            continue
        
        # Collect all values for both models
        all_vals_m1 = []
        all_vals_m2 = []
        
        for temp in common_temps:
            for temp_dict in data_model1[metric].values():
                if temp in temp_dict:
                    all_vals_m1.extend(temp_dict[temp])
            
            for temp_dict in data_model2[metric].values():
                if temp in temp_dict:
                    all_vals_m2.extend(temp_dict[temp])
        
        if len(all_vals_m1) < 3 or len(all_vals_m2) < 3:
            continue
        
        # Perform statistical test
        try:
            # Use Mann-Whitney U test (non-parametric)
            statistic, p_value = stats.mannwhitneyu(all_vals_m1, all_vals_m2, alternative='two-sided')
            
            # Calculate effect size (Cohen's d)
            pooled_std = np.sqrt(((len(all_vals_m1) - 1) * np.var(all_vals_m1, ddof=1) + 
                                 (len(all_vals_m2) - 1) * np.var(all_vals_m2, ddof=1)) / 
                                (len(all_vals_m1) + len(all_vals_m2) - 2))
            
            if pooled_std > 0:
                cohens_d = (np.mean(all_vals_m2) - np.mean(all_vals_m1)) / pooled_std
            else:
                cohens_d = 0
            
            metrics_tested.append(metric)
            p_values.append(p_value)
            effect_sizes.append(abs(cohens_d))
            
            # Determine which model performs better
            if np.mean(all_vals_m2) > np.mean(all_vals_m1):
                if metric in ERROR_METRICS:
                    better_model.append(MODEL_1_NAME)  # Lower error is better
                else:
                    better_model.append(MODEL_2_NAME)  # Higher performance is better
            else:
                if metric in ERROR_METRICS:
                    better_model.append(MODEL_2_NAME)
                else:
                    better_model.append(MODEL_1_NAME)
            
            comparison_results[metric] = {
                'p_value': p_value,
                'effect_size': cohens_d,
                'model1_mean': np.mean(all_vals_m1),
                'model2_mean': np.mean(all_vals_m2),
                'significant': p_value < 0.05,
                'better_model': better_model[-1]
            }
            
        except Exception as e:
            print(f"Statistical test failed for {metric}: {e}")
            continue
    
    # Plot 1: P-values
    colors = ['red' if p < 0.05 else 'blue' for p in p_values]
    ax1.barh(range(len(metrics_tested)), p_values, color=colors, alpha=0.7)
    ax1.axvline(x=0.05, color='red', linestyle='--', label='α = 0.05')
    ax1.set_yticks(range(len(metrics_tested)))
    ax1.set_yticklabels([m.replace('_', ' ').title() for m in metrics_tested])
    ax1.set_xlabel('P-value (Mann-Whitney U Test)')
    ax1.set_title('Statistical Significance of Model Differences')
    ax1.set_xscale('log')
    ax1.legend()
    
    # Plot 2: Effect sizes with better model annotation
    effect_colors = ['green' if better == MODEL_2_NAME else 'orange' for better in better_model]
    bars = ax2.barh(range(len(metrics_tested)), effect_sizes, color=effect_colors, alpha=0.7)
    ax2.set_yticks(range(len(metrics_tested)))
    ax2.set_yticklabels([m.replace('_', ' ').title() for m in metrics_tested])
    ax2.set_xlabel('Effect Size (|Cohen\'s d|)')
    ax2.set_title('Effect Size of Model Differences')
    
    # Add better model annotations
    for i, (bar, better) in enumerate(zip(bars, better_model)):
        width = bar.get_width()
        ax2.text(width + max(effect_sizes) * 0.01, bar.get_y() + bar.get_height()/2, 
                better, ha='left', va='center', fontsize=9, fontweight='bold')
    
    # Add legend for colors
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='green', alpha=0.7, label=f'{MODEL_2_NAME} Better'),
                      Patch(facecolor='orange', alpha=0.7, label=f'{MODEL_1_NAME} Better')]
    ax2.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(f"{COMPARISON_OUTPUT_DIR}/statistical_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: statistical_comparison.png")
    
    return comparison_results

def create_temperature_sensitivity_analysis():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    model_sensitivities = {MODEL_1_NAME: [], MODEL_2_NAME: []}
    metric_names = []
    
    for metric in TARGET_METRICS:
        # Calculate temperature sensitivity for each model
        for model_name, data in [(MODEL_1_NAME, data_model1), (MODEL_2_NAME, data_model2)]:
            temps = set()
            for temp_dict in data[metric].values():
                temps.update(temp_dict.keys())
            temps = sorted(temps)
            
            if len(temps) < 3:
                model_sensitivities[model_name].append(0)
                continue
            
            # Calculate coefficient of variation across temperatures
            temp_means = []
            for temp in temps:
                temp_values = []
                for temp_dict in data[metric].values():
                    if temp in temp_dict:
                        temp_values.extend(temp_dict[temp])
                if temp_values:
                    temp_means.append(np.mean(temp_values))
            
            if len(temp_means) > 1 and np.mean(temp_means) != 0:
                cv = np.std(temp_means, ddof=1) / abs(np.mean(temp_means))
                model_sensitivities[model_name].append(cv)
            else:
                model_sensitivities[model_name].append(0)
        
        metric_names.append(metric.replace('_', ' ').title())
    
    # Plot sensitivity comparison
    x = np.arange(len(metric_names))
    width = 0.35
    
    ax1.bar(x - width/2, model_sensitivities[MODEL_1_NAME], width, 
           label=MODEL_1_NAME, alpha=0.7)
    ax1.bar(x + width/2, model_sensitivities[MODEL_2_NAME], width, 
           label=MODEL_2_NAME, alpha=0.7)
    
    ax1.set_xlabel('Metrics')
    ax1.set_ylabel('Temperature Sensitivity (CV)')
    ax1.set_title('Temperature Sensitivity by Model')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metric_names, rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Overall sensitivity comparison
    overall_sens_m1 = np.mean([s for s in model_sensitivities[MODEL_1_NAME] if s > 0])
    overall_sens_m2 = np.mean([s for s in model_sensitivities[MODEL_2_NAME] if s > 0])
    
    ax2.bar([MODEL_1_NAME, MODEL_2_NAME], [overall_sens_m1, overall_sens_m2], 
           color=['orange', 'green'], alpha=0.7)
    ax2.set_ylabel('Average Temperature Sensitivity')
    ax2.set_title('Overall Temperature Sensitivity')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    ax2.text(0, overall_sens_m1 + max(overall_sens_m1, overall_sens_m2) * 0.02, 
            f'{overall_sens_m1:.3f}', ha='center', va='bottom', fontweight='bold')
    ax2.text(1, overall_sens_m2 + max(overall_sens_m1, overall_sens_m2) * 0.02, 
            f'{overall_sens_m2:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{COMPARISON_OUTPUT_DIR}/temperature_sensitivity.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: temperature_sensitivity.png")

def create_comprehensive_summary():
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
    
    # Main comparison plot (spans 2x2)
    ax_main = fig.add_subplot(gs[0:2, 0:2])
    
    # Get overall performance scores
    temps = sorted(set().union(
        *[temp_dict.keys() for metric_data in data_model1.values() for temp_dict in metric_data.values()],
        *[temp_dict.keys() for metric_data in data_model2.values() for temp_dict in metric_data.values()]
    ))
    
    # Calculate overall performance scores (performance metrics - error metrics)
    overall_m1 = []
    overall_m2 = []
    
    for temp in temps:
        # Model 1 score
        perf_vals_m1 = []
        error_vals_m1 = []
        for metric in PERFORMANCE_METRICS:
            for temp_dict in data_model1[metric].values():
                if temp in temp_dict:
                    perf_vals_m1.extend(temp_dict[temp])
        for metric in ERROR_METRICS:
            for temp_dict in data_model1[metric].values():
                if temp in temp_dict:
                    error_vals_m1.extend(temp_dict[temp])
        
        # Model 2 score
        perf_vals_m2 = []
        error_vals_m2 = []
        for metric in PERFORMANCE_METRICS:
            for temp_dict in data_model2[metric].values():
                if temp in temp_dict:
                    perf_vals_m2.extend(temp_dict[temp])
        for metric in ERROR_METRICS:
            for temp_dict in data_model2[metric].values():
                if temp in temp_dict:
                    error_vals_m2.extend(temp_dict[temp])
        
        if perf_vals_m1 and error_vals_m1:
            overall_m1.append(np.mean(perf_vals_m1) - np.mean(error_vals_m1))
        else:
            overall_m1.append(np.nan)
            
        if perf_vals_m2 and error_vals_m2:
            overall_m2.append(np.mean(perf_vals_m2) - np.mean(error_vals_m2))
        else:
            overall_m2.append(np.nan)
    
    ax_main.plot(temps, overall_m1, 'o-', linewidth=3, markersize=8, label=MODEL_1_NAME)
    ax_main.plot(temps, overall_m2, 's-', linewidth=3, markersize=8, label=MODEL_2_NAME)
    ax_main.set_title('Overall Performance Comparison\n(Performance - Error Score)', fontsize=14, fontweight='bold')
    ax_main.set_xlabel('Temperature')
    ax_main.set_ylabel('Net Performance Score')
    ax_main.legend(fontsize=12)
    ax_main.grid(True, alpha=0.3)
    
    # Additional smaller plots
    # You can add more specific comparisons here
    
    plt.suptitle(f'Comprehensive Model Comparison: {MODEL_1_NAME} vs {MODEL_2_NAME}', 
                fontsize=16, fontweight='bold')
    plt.savefig(f"{COMPARISON_OUTPUT_DIR}/comprehensive_summary.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: comprehensive_summary.png")

def main():
    global data_model1, data_model2
    
    print("Loading model data...")
    data_model1, counts_model1 = load_model_data(MODEL_1_DIR, MODEL_1_NAME)
    data_model2, counts_model2 = load_model_data(MODEL_2_DIR, MODEL_2_NAME)
    
    print("Creating visualizations...")
    create_side_by_side_comparison()
    create_difference_heatmap()
    comparison_results = create_statistical_comparison()
    create_temperature_sensitivity_analysis()
    create_comprehensive_summary()
    
    # Print summary
    print(f"Models compared: {MODEL_1_NAME} vs {MODEL_2_NAME}")
    print(f"Temperature ranges: {sorted(counts_model1.keys())} vs {sorted(counts_model2.keys())}")
    
    if comparison_results:
        print("\nStatistical Comparison Results:")
        for metric, result in comparison_results.items():
            significance = "SIGNIFICANT" if result['significant'] else "NOT SIGNIFICANT"
            print(f"{metric}: {result['better_model']} performs better ({significance}, p={result['p_value']:.4f})")
    
    print(f"\nAll comparison plots saved to: {COMPARISON_OUTPUT_DIR}")

if __name__ == "__main__":
    main()