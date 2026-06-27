"""
Evaluation Agent - Computes performance metrics for the business analyst agent pipeline.

Metrics include:
- LLM accuracy by comparing summary.md values against pandas ground truth
- LLM fallback rate from call logs
- Pipeline timing and slowest agent identification
- Chart validation retry counts
- Security scan status and timing
- Total LLM tokens consumed
"""

import pandas as pd
import json
import re
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_agent(csv_filepath, audit_log_path="audit.log", llm_call_log=[]):
    """
    Evaluate agent pipeline performance based on CSV data, LLM outputs, and audit logs.
    
    Args:
        csv_filepath (str): Path to CSV file for computing ground truth statistics
        audit_log_path (str): Path to audit log file (default: "audit.log")
        llm_call_log (list): List of LLM call records, each with 'tokens' and 'response' fields
    
    Returns:
        dict: Evaluation report containing all computed metrics
    
    Raises:
        FileNotFoundError: If csv_filepath does not exist
    """
    
    # Log start
    logger.info(f"Starting EvalAgent for {csv_filepath}")
    with open(audit_log_path, 'a') as f:
        f.write(f"{datetime.now().isoformat()} - EvalAgent - START\n")
    
    try:
        # 1. Compute pandas ground truth statistics
        df = pd.read_csv(csv_filepath)
        ground_truth = _compute_ground_truth(df)
        logger.info(f"Computed ground truth for {len(ground_truth)} numeric columns")
        
        # 2. Parse summary.md and compute LLM accuracy
        llm_accuracy_score = _compute_llm_accuracy(ground_truth)
        logger.info(f"LLM accuracy score: {llm_accuracy_score}")
        
        # 3. Compute LLM fallback rate from call log
        llm_fallback_rate = _compute_fallback_rate(llm_call_log)
        logger.info(f"LLM fallback rate: {llm_fallback_rate}")
        
        # 4. Parse audit.log for timing and agent metrics
        audit_data = _parse_audit_log(audit_log_path)
        logger.info(f"Parsed audit log: slowest_agent={audit_data['slowest_agent']}, "
                   f"retries={audit_data['chart_validation_retries']}")
        
        # 5. Compute total LLM tokens
        total_llm_tokens = _compute_total_tokens(llm_call_log)
        logger.info(f"Total LLM tokens: {total_llm_tokens}")
        
        # 6. Build evaluation report with exact specified keys
        eval_report = {
            'pipeline_duration_sec': audit_data['pipeline_duration_sec'],
            'slowest_agent': audit_data['slowest_agent'],
            'slowest_agent_sec': audit_data['slowest_agent_sec'],
            'llm_accuracy_score': llm_accuracy_score,
            'llm_fallback_rate': llm_fallback_rate,
            'chart_validation_retries': audit_data['chart_validation_retries'],
            'security_status': audit_data['security_status'],
            'security_scan_time_sec': audit_data['security_scan_time_sec'],
            'total_llm_tokens': total_llm_tokens
        }
        
        # 7. Save evaluation report
        output_path = Path('outputs/eval_report.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(eval_report, f, indent=2)
        
        logger.info(f"Evaluation report saved to {output_path}")
        
        # Log completion
        with open(audit_log_path, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - EvalAgent - COMPLETED\n")
        
        return eval_report
    
    except Exception as e:
        logger.error(f"Error in EvalAgent: {str(e)}", exc_info=True)
        with open(audit_log_path, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - EvalAgent - FAILED: {str(e)}\n")
        raise


def _compute_ground_truth(df):
    """
    Compute ground truth statistics (mean, std, skewness, kurtosis) for numeric columns.
    
    Args:
        df (pd.DataFrame): Input dataframe
    
    Returns:
        dict: Statistics keyed by column name
    """
    ground_truth = {}
    
    for col in df.select_dtypes(include=['number']).columns:
        ground_truth[col] = {
            'mean': float(df[col].mean()),
            'std': float(df[col].std()),
            'skewness': float(df[col].skew()),
            'kurtosis': float(df[col].kurtosis())
        }
    
    return ground_truth


def _compute_llm_accuracy(ground_truth):
    """
    Parse summary.md for numeric values and compare against ground truth with ±5% tolerance.
    
    Args:
        ground_truth (dict): Ground truth statistics from pandas
    
    Returns:
        float or None: Accuracy percentage (matching_claims / total_claims) * 100, or None if no summary
    """
    summary_md_path = Path('outputs/summary.md')
    
    if not summary_md_path.exists():
        logger.warning(f"Summary file not found: {summary_md_path}")
        return None
    
    try:
        with open(summary_md_path, 'r', encoding='utf-8', errors='ignore') as f:
            summary_content = f.read()

        # First, try parsing EDA markdown table rows like:
        # | **col1** | 0.5028 | 0.1465 | 0.0978 | -0.0084 |
        # or
        # | `col1` | 0.5028 | 0.1465 | 0.0978 | -0.0084 |
        table_pattern = r"\|\s*[`*]{0,2}(col\w+)[`*]{0,2}\s*\|\s*([\d.]+)\s*\|\s*[\d.]+\s*\|\s*([\d.]+)\s*\|\s*([–\-]?[\d.]+)\s*\|\s*([–\-]?[\d.]+)\s*\|"
        table_matches = list(re.finditer(table_pattern, summary_content, re.MULTILINE))

        total_claims = 0
        matching_claims = 0

        if table_matches:
            for m in table_matches:
                col = m.group(1).strip()
                # normalize dash characters to ASCII minus
                def norm(x):
                    return x.replace('\u2013', '-').replace('\u2014', '-').replace('–', '-').replace('—', '-')

                try:
                    mean_val = float(norm(m.group(2)))
                    std_val = float(norm(m.group(3)))
                    skew_val = float(norm(m.group(4)))
                    kurt_val = float(norm(m.group(5)))
                except ValueError:
                    continue

                if col not in ground_truth:
                    continue

                stats = ground_truth[col]
                for metric_name, extracted_value in (('mean', mean_val), ('std', std_val), ('skewness', skew_val), ('kurtosis', kurt_val)):
                    gt_value = stats.get(metric_name)
                    if gt_value is None:
                        continue
                    total_claims += 1
                    tolerance = abs(gt_value) * 0.05
                    if abs(extracted_value - gt_value) <= tolerance:
                        matching_claims += 1

            if total_claims == 0:
                logger.info("No matching EDA table claims found in summary.md")
                return None

            accuracy = (matching_claims / total_claims) * 100
            logger.info(f"LLM accuracy: {matching_claims}/{total_claims} claims match ground truth")
            return accuracy

        # Fallback: parse simple "metric: value" claims as before
        pattern = r'(mean|std|skewness|kurtosis)\s*(?:of\s+[\w\s]+\s*)?[\:=]\s*([-\d\.\u2013\u2014–—]+)'
        matches = re.findall(pattern, summary_content, re.IGNORECASE)

        if not matches:
            logger.info("No numeric claims found in summary.md")
            return None

        total_claims = len(matches)
        matching_claims = 0

        for metric, value_str in matches:
            metric_lower = metric.lower()
            try:
                value_str_norm = value_str.replace('\u2013', '-').replace('\u2014', '-').replace('–', '-').replace('—', '-')
                extracted_value = float(value_str_norm)

                # Find matching ground truth value
                for col, stats in ground_truth.items():
                    if metric_lower in stats:
                        gt_value = stats[metric_lower]
                        tolerance = abs(gt_value) * 0.05
                        if abs(extracted_value - gt_value) <= tolerance:
                            matching_claims += 1
                            break

            except ValueError:
                pass

        accuracy = (matching_claims / total_claims) * 100 if total_claims > 0 else None
        logger.info(f"LLM accuracy: {matching_claims}/{total_claims} claims match ground truth")
        return accuracy

    except Exception as e:
        logger.error(f"Error computing LLM accuracy: {str(e)}")
        return None


def _compute_fallback_rate(llm_call_log):
    """
    Compute fallback rate from LLM call log (failed / total calls).
    
    Args:
        llm_call_log (list): List of LLM call records with 'response' field
    
    Returns:
        float or None: Fallback rate percentage, or None if log is empty
    """
    if not llm_call_log:
        return None
    
    total_calls = len(llm_call_log)
    failed_calls = 0
    
    for call in llm_call_log:
        response = call.get('response')
        # Failed if response is empty, None, invalid JSON, or whitespace-only string
        if not response or (isinstance(response, str) and not response.strip()):
            failed_calls += 1
    
    fallback_rate = (failed_calls / total_calls) * 100 if total_calls > 0 else None
    logger.info(f"LLM fallback rate: {failed_calls}/{total_calls} failed calls")
    return fallback_rate


def _parse_audit_log(audit_log_path):
    """
    Parse audit log to extract:
    - Pipeline duration (first to last timestamp)
    - Slowest agent and its duration
    - Chart validation retry count
    - Security scan status and duration
    
    Args:
        audit_log_path (str): Path to audit log file
    
    Returns:
        dict: Parsed metrics with None values for unavailable data
    """
    result = {
        'pipeline_duration_sec': None,
        'slowest_agent': None,
        'slowest_agent_sec': None,
        'chart_validation_retries': 0,
        'security_status': None,
        'security_scan_time_sec': None
    }
    
    try:
        if not Path(audit_log_path).exists():
            logger.warning(f"Audit log not found: {audit_log_path}")
            return result

        with open(audit_log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        if not lines:
            return result

        timestamps = []
        agent_timings = {}

        # Find the last occurrence of the SecurityValidatorAgent run
        last_security_run_idx = None
        for i, l in enumerate(lines):
            if re.search(r'Running\s+SecurityValidatorAgent', l):
                last_security_run_idx = i

        # Determine processing start index: start from last security run if found, else from beginning
        start_idx = last_security_run_idx if last_security_run_idx is not None else 0

        # Track chart attempts and security window within the current run
        chart_attempt_numbers = []
        security_start_ts = None
        security_end_ts = None

        for idx in range(start_idx, len(lines)):
            line = lines[idx]
            # Try ISO format first (with optional timezone)
            iso_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:[\.\d]*)?(?:[+-]\d{4})?)', line)
            log_match = None
            ts = None

            try:
                if iso_match:
                    ts_str = iso_match.group(1)
                    # Parse ISO with possible timezone then drop tzinfo to make naive
                    ts = datetime.fromisoformat(ts_str).replace(tzinfo=None)
                else:
                    # Try standard logger format: 2026-06-24 18:41:07,530
                    log_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
                    if log_match:
                        ts_str = log_match.group(1)
                        ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S,%f")

                if not ts:
                    continue

                timestamps.append(ts)

                # Detect start of SecurityValidatorAgent run (within current run)
                if re.search(r'Running\s+SecurityValidatorAgent', line):
                    security_start_ts = ts

                # Track agent start times from "Running XAgent" (capture base name before 'Agent')
                run_match = re.search(r'Running\s+([A-Za-z0-9_]+)Agent', line)
                if run_match:
                    base = run_match.group(1)
                    agent_name_key = f"{base}Agent"
                    if agent_name_key not in agent_timings:
                        agent_timings[agent_name_key] = {}
                    agent_timings[agent_name_key]['start'] = ts

                # Track agent end from patterns like "XAgent: ...complete" or "XAgent completed"
                end_match = re.search(r'([A-Za-z0-9_]+)Agent[:\s].*complete', line, re.IGNORECASE) or re.search(r'([A-Za-z0-9_]+)Agent\s+completed', line, re.IGNORECASE)
                if end_match:
                    base = end_match.group(1)
                    agent_name_key = f"{base}Agent"
                    if agent_name_key not in agent_timings:
                        agent_timings[agent_name_key] = {}
                    agent_timings[agent_name_key]['end'] = ts

                # Count chart validation attempt numbers only after last security run
                if last_security_run_idx is not None and idx > last_security_run_idx and re.search(r'Chart validation attempt', line, re.IGNORECASE):
                    attempt_match = re.search(r'Chart validation attempt\s*(\d+)', line, re.IGNORECASE)
                    if attempt_match:
                        try:
                            chart_attempt_numbers.append(int(attempt_match.group(1)))
                        except ValueError:
                            pass

                # Track Security validation result lines
                if re.search(r'Security validation', line, re.IGNORECASE):
                    if re.search(r'PASSED', line, re.IGNORECASE):
                        result['security_status'] = 'PASSED'
                        security_end_ts = ts
                    elif re.search(r'BLOCKED', line, re.IGNORECASE):
                        result['security_status'] = 'BLOCKED'
                        security_end_ts = ts

            except Exception:
                # Ignore parse errors for individual lines
                continue

        # Compute chart_validation_retries from attempt numbers (max - 1)
        if chart_attempt_numbers:
            try:
                max_attempt = max(chart_attempt_numbers)
                result['chart_validation_retries'] = max(0, max_attempt - 1)
            except Exception:
                result['chart_validation_retries'] = 0

        # Compute SecurityAgent scan time if both start and end timestamps found
        if security_start_ts and security_end_ts:
            try:
                result['security_scan_time_sec'] = (security_end_ts - security_start_ts).total_seconds()
            except Exception:
                result['security_scan_time_sec'] = None
        
        # Calculate pipeline duration (first to last timestamp)
        if len(timestamps) >= 2:
            result['pipeline_duration_sec'] = (timestamps[-1] - timestamps[0]).total_seconds()
        
        # Find slowest agent
        max_duration = 0
        for agent_name, times in agent_timings.items():
            if 'start' in times and 'end' in times:
                duration = (times['end'] - times['start']).total_seconds()
                if duration > max_duration:
                    max_duration = duration
                    result['slowest_agent'] = agent_name
                    result['slowest_agent_sec'] = duration
        
    
    except Exception as e:
        logger.error(f"Error parsing audit log: {str(e)}", exc_info=True)
    
    return result


def _compute_total_tokens(llm_call_log):
    """
    Sum all 'tokens' fields from LLM call log.
    
    Args:
        llm_call_log (list): List of LLM call records with 'tokens' field
    
    Returns:
        int or None: Total token count, or None if log is empty or tokens unavailable
    """
    if not llm_call_log:
        return None
    
    total = 0
    has_tokens = False
    
    for call in llm_call_log:
        tokens = call.get('tokens')
        if isinstance(tokens, (int, float)):
            total += tokens
            has_tokens = True
    
    return total if has_tokens else None
