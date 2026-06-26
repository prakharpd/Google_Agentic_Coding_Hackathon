## **Dataset Overview**
- **Shape**: 10 rows × 5 columns  
- **Columns**: `col1`, `col2`, `col3`, `col4`, `col5`  
- **Column Count**: 5  
- **Data Types**  
  - `col1`: float64  
  - `col2`: float64  
  - `col3`: float64  
  - `col4`: float64  
  - `col5`: float64  
- **Null Value Counts**  
  - `col1`: 0  
  - `col2`: 0  
  - `col3`: 0  
  - `col4`: 0  
  - `col5`: 0  
- **Numeric Ranges**  
  - `col1`: min = 0.0871, max = 0.9786  
  - `col2`: min = 0.0202, max = 0.7992  
  - `col3`: min = 0.1289, max = 0.9447  
  - `col4`: min = 0.0602, max = 0.9637  
  - `col5`: min = 0.0188, max = 0.8700  

## **EDA Findings Per Column**
| Column | Mean | Std Dev | Skewness | Kurtosis |
|--------|------|---------|----------|----------|
| **col1** | 0.5604 | 0.2469 | -0.4091 | 0.0951 |
| **col2** | 0.4678 | 0.2575 | -0.3988 | -1.0964 |
| **col3** | 0.6201 | 0.2295 | -0.6155 | 0.6444 |
| **col4** | 0.6403 | 0.2805 | -0.7622 | -0.0175 |
| **col5** | 0.4012 | 0.2658 | 0.1844 | -0.8299 |

## **Chart Descriptions**
- **col1_histogram.png** – Histogram of `col1`; left‑skewed distribution with most values above the mean.  
- **col2_histogram.png** – Histogram of `col2`; moderate spread and a slight left‑hand tail.  
- **col3_histogram.png** – Histogram of `col3`; left‑skewed with a tight peak around the mean.  
- **col4_histogram.png** – Histogram of `col4`; most pronounced left skew and high variability.  
- **col5_histogram.png** – Histogram of `col5`; moderate spread and a faint right‑hand tail.  

## **Top 3 Business Insights**
1. **Consistent Left‑Skew Across Most Variables** – The negative skewness in `col1`–`col4` indicates that most observations are above the mean, with a few low outliers. This could point to a general high‑performance baseline that occasionally dips, requiring targeted improvement actions.  
2. **High Variability in `col4`** – The largest standard deviation (0.2805) suggests significant dispersion, implying that this metric may represent a business area with widely varying outcomes (e.g., customer satisfaction or sales conversion). Segmenting or tailoring strategies could help manage this volatility.  
3. **Stable Baseline in `col5`** – The slight positive skew and negative kurtosis give this variable a more symmetrical, light‑tailed shape, indicating consistent performance. It could serve as a reliable benchmark against which other columns are evaluated.

## **Data Quality Notes**
- **Completeness** – All fields are fully populated; null counts are zero.  
- **Outliers** – Negative skewness in several columns indicates low‑value outliers that could distort the mean.  
- **Cleaning Recommendations**  
  1. **Outlier Mitigation** – Apply winsorization at the 5th/95th percentiles for columns with high skewness.  
  2. **Transformation** – Consider log/Box‑Cox transformation on highly skewed features to stabilise variance for modelling.  
  3. **Re‑evaluation** – After cleaning, re‑compute descriptive statistics to confirm that business‑relevant patterns remain intact.