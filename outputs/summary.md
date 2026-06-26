## **Dataset Overview**

- **Shape**: 2000 samples × 5 variables  
- **Column count**: 5  
- **Data types**  
  - `col1_normal`: `float64`  
  - `col2_right_skewed`: `float64`  
  - `col3_left_skewed`: `float64`  
  - `col4_bimodal`: `float64`  
  - `col5_uniform`: `float64`  
- **Null values**: No missing values in any column  
- **Numeric ranges**  
  - `col1_normal`: 0.0 – 1.0  
  - `col2_right_skewed`: 0.0002 – 1.0  
  - `col3_left_skewed`: 0.0 – 1.0  
  - `col4_bimodal`: 0.0 – 0.968  
  - `col5_uniform`: 0.0012 – 0.9999  

---

## **EDA Findings Per Column**

- **`col1_normal`**  
  - Mean: 0.4917 Median: 0.4886 Std: 0.1494  
  - Skewness: 0.102 Kurtosis: 0.043  
- **`col2_right_skewed`**  
  - Mean: 0.2526 Median: 0.1818 Std: 0.2330  
  - Skewness: 1.346 Kurtosis: 1.336  
- **`col3_left_skewed`**  
  - Mean: 0.7498 Median: 0.8204 Std: 0.2298  
  - Skewness: –1.353 Kurtosis: 1.454  
- **`col4_bimodal`**  
  - Mean: 0.4998 Median: 0.5234 Std: 0.2598  
  - Skewness: –0.009 Kurtosis: –1.636  
- **`col5_uniform`**  
  - Mean: 0.4980 Median: 0.5032 Std: 0.2867  
  - Skewness: –0.012 Kurtosis: –1.194  

---

## **Chart Descriptions**

1. **col1_normal_histogram.png** – Displays a symmetric bell‑shaped distribution centered at ~0.5, confirming normality.  
2. **col2_right_skewed_histogram.png** – Highlights a long right tail; majority of observations cluster near 0, with a few high outliers up to 1.  
3. **col3_left_skewed_histogram.png** – Opposite of #2: a left‑skewed shape with most mass near 1 and a tail extending toward lower values.  
4. **col4_bimodal_histogram.png** – Shows two distinct peaks (bimodality) near 0.25 and 0.75, indicating potential sub‑populations.  
5. **col5_uniform_histogram.png** – Exhibits near‑uniform coverage across the 0–1 interval, as expected for a uniform distribution.  

---

## **Top 3 Business Insights**

1. **Skewed Behaviors Signal Underlying Sub‑Groups**  
   - `col2_right_skewed` and `col3_left_skewed` reveal asymmetric processes (e.g., high‑frequency low‑value events versus rare high‑value events).  
   - These asymmetries could reflect customer spending patterns or operational metrics that warrant targeted interventions.  

2. **Bimodality Indicates Divergent Segments**  
   - `col4_bimodal` suggests the presence of two distinct operational or customer segments.  
   - Further segmentation analysis could uncover differing value drivers or risk profiles.  

3. **Uniform Distribution Highlights Homogeneity**  
   - `col5_uniform` indicates highly consistent behavior across the sample, potentially serving as a baseline or control variable in predictive modeling.  

---

## **Data Quality Notes**

- **Completeness**: The dataset is fully populated; no nulls detected, mitigating missing‑data bias.  
- **Outliers & Extreme Values**:  
  - High skewness in `col2_right_skewed` and `col3_left_skewed` suggests the presence of outliers that may distort modeling if not addressed.  
  - The bimodal peak separation in `col4_bimodal` indicates heterogeneous influences rather than single outliers.  
- **Recommended Cleaning Steps**  
  - **Outlier Treatment**: Apply winsorization or robust scaling for highly skewed columns to prevent model distortion.  
  - **Transformations**: Log or Box‑Cox transforms can normalize `col2_right_skewed` and `col3_left_skewed`, improving distributional assumptions.  
  - **Segmentation**: For `col4_bimodal`, consider clustering (e.g., k‑means) to isolate sub‑groups prior to further analysis.  
  - **Validation**: Re‑calculate key statistics post‑cleaning to confirm improved symmetry/kurtosis levels.

These steps will enhance the reliability of downstream analytical models and support more accurate business decision‑making.