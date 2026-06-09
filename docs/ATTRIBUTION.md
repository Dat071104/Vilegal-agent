# Attribution Requirements

> **DISCLAIMER:** This document provides technical guidance for dataset attribution within the ViLegal Agent project. It does not constitute legal advice. If in doubt, consult a legal professional regarding compliance with open-source licenses and Vietnamese data usage laws.

This document outlines the required attribution templates for datasets utilized in this project. All downstream artifacts, models, or publications derived from these datasets must include the appropriate attributions.

## License Templates

### MIT License
Attribution is appreciated but not legally strictly required by the license itself for mere usage. However, for academic and open-source integrity, we adhere to the following template:
> This project utilizes data from [Dataset Name] ([Dataset URL]), licensed under the MIT License.

### CC-BY-4.0 (Creative Commons Attribution 4.0 International)
Attribution is **REQUIRED**. Any downstream use, redistribution, or derivation must give appropriate credit, provide a link to the license, and indicate if changes were made.
> This work uses data from [Dataset Name] ([Dataset URL]), which is made available under the Creative Commons Attribution 4.0 International License (CC-BY-4.0).

---

## Dataset-Specific Snippets

The following snippets must be included in the project's main `README.md` or any public-facing model card once bulk ingestion is approved.

### 1. `undertheseanlp/UTS_VLC`
- **License:** MIT (CONFIRMED)
- **Attribution Status:** Appreciated
- **Snippet:**
  ```text
  This project utilizes the UTS_VLC dataset (https://huggingface.co/datasets/undertheseanlp/UTS_VLC) curated by undertheseanlp, made available under the MIT License.
  ```

### 2. `duyet/vietnamese-legal-instruct`
- **License:** CC-BY-4.0 (CONFIRMED)
- **Attribution Status:** REQUIRED
- **Snippet:**
  ```text
  This work incorporates instructional data from duyet/vietnamese-legal-instruct (https://huggingface.co/datasets/duyet/vietnamese-legal-instruct). This dataset is licensed under the Creative Commons Attribution 4.0 International License (CC-BY-4.0).
  ```
- **Notes:** This dataset contains AI-generated instruction pairs and is NOT treated as legal ground truth.

### 3. `th1nhng0/vietnamese-legal-documents`
- **License:** CC-BY-4.0 (CONFIRMED)
- **Attribution Status:** REQUIRED
- **Snippet:**
  ```text
  This project utilizes the vietnamese-legal-documents dataset (https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents) created by th1nhng0, licensed under the Creative Commons Attribution 4.0 International License (CC-BY-4.0).
  ```
