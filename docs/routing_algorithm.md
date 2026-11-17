# Proposed Query-Driven Model Routing Formulation

## 1. Motivation
Traditional remote-sensing AI architectures operate under rigid assumptions: single-image VQA models cannot evaluate bi-temporal changes; optical change-detection networks fail on polarimetric radar data; and optical-SAR fusion networks cannot digest arbitrary single-band optical rasters without modification.

To solve this task fragmentation, SatQuery AI implements a multi-objective scoring formulation that evaluates candidate foundation specialists across six distinct criteria.

## 2. Mathematical Formulation

For a given user query $q$, input asset collection $\mathcal{I} = \{I_1, I_2, \dots, I_N\}$, and candidate specialist model $m \in \mathcal{M}$, the routing score $\text{Score}(q, m)$ is defined as:

$$\text{Score}(q, m) = w_1 \cdot \text{TaskMatch}(q, m) + w_2 \cdot \text{InputTypeMatch}(\mathcal{I}, m) + w_3 \cdot \text{ModalityMatch}(\mathcal{I}, m) + w_4 \cdot \text{CapabilityMatch}(q, m) + w_5 \cdot \text{Compatibility}(\mathcal{I}) + w_6 \cdot \text{Availability}(m)$$

Subject to the normalization constraint:
$$\sum_{i=1}^6 w_i = 1.0, \quad w_i \ge 0$$

### Default Configuration Weights
| Weight Parameter | Component | Default Value | Rationale |
|---|---|---|---|
| $w_1$ | `TaskMatch` | 0.25 | Primary alignment between query intent and specialist task specialization |
| $w_2$ | `InputTypeMatch` | 0.20 | Structural conformity to single, bi-temporal, or optical-SAR pair inputs |
| $w_3$ | `ModalityMatch` | 0.15 | Sensor spectral / polarimetric match (Optical, SAR, Multispectral) |
| $w_4$ | `CapabilityMatch` | 0.15 | Specific downstream capability (Dense change masks, visual bounding boxes) |
| $w_5$ | `Compatibility` | 0.15 | Spatial aspect ratio, dimension alignment, CRS, and temporal consistency |
| $w_6$ | `Availability` | 0.10 | Active operational status of the model endpoint (Available vs Mock vs Offline) |

## 3. Mathematical Term Definitions

### 3.1 Task Match ($\text{TaskMatch}$)
$$\text{TaskMatch}(q, m) = \begin{cases} 
1.0 & \text{if } \text{Task}(q) \in \text{Tasks}(m) \\
0.75 & \text{if } \text{Task}(q) \in \{\text{CAPTIONING}, \text{SCENE}\} \land \text{VQA} \in \text{Tasks}(m) \\
0.85 & \text{if } \text{Task}(q) = \text{CHANGE\_VQA} \land \text{CHANGE\_DETECTION} \in \text{Tasks}(m) \\
0.0 & \text{otherwise}
\end{cases}$$

### 3.2 Input Type Match ($\text{InputTypeMatch}$)
$$\text{InputTypeMatch}(\mathcal{I}, m) = \begin{cases} 
1.0 & \text{if } \text{Type}(\mathcal{I}) \in \text{InputTypes}(m) \\
0.0 & \text{otherwise}
\end{cases}$$

### 3.3 Modality Match ($\text{ModalityMatch}$)
$$\text{ModalityMatch}(\mathcal{I}, m) = \begin{cases} 
1.0 & \text{if } \text{Modality}(\mathcal{I}) \in \text{Modalities}(m) \lor \text{UNKNOWN} \in \text{Modalities}(m) \\
0.9 & \text{if } \text{Modality}(\mathcal{I}) = \text{OPTICAL} \land \text{MULTISPECTRAL} \in \text{Modalities}(m) \\
0.0 & \text{otherwise}
\end{cases}$$

### 3.4 Domain Consistency Gate
Prior to scoring, the engine evaluates domain consistency gates:
- **Bi-Temporal Invariance**: If $\text{Task}(q) \in \{\text{CHANGE\_DETECTION}, \text{CHANGE\_VQA}\}$ and $|\mathcal{I}| < 2$, execution is halted with an informative explanation rather than misrouted.
- **Multimodal Invariance**: If $\text{Task}(q) = \text{OPTICAL\_SAR\_ANALYSIS}$, the asset collection must contain distinct optical and radar modalities.
