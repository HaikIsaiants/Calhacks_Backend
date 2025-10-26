{
  "savedAt": "2025-11-02T12:05:00.000Z",
  "changes": {
    "documentHtml": "<h1>Endotoxin Rescue Screen</h1><p>CRISPRi of TLR4 preserves viability (88%) but macrophages stall on MDR <em>Pseudomonas</em> clearance.</p><p>Plan follow-up loop edits on TLR4/MD-2 to bias signaling toward TRIF while retaining pathogen recognition.</p>",
    "sequenceBlocks": [
      {
        "id": "seq-tlr4-donor",
        "x": 90,
        "y": 228
      }
    ],
    "tables": {
      "table-killcurve": {
        "columns": [
          "Condition",
          "Bacteria_CFUs",
          "TNF_pg_ml",
          "Viability_percent"
        ],
        "rows": [
          {
            "id": 1,
            "Condition": "TLR4 CRISPRi",
            "Bacteria_CFUs": 2700000.0,
            "TNF_pg_ml": 186.0,
            "Viability_percent": 88.4
          },
          {
            "id": 2,
            "Condition": "NTC",
            "Bacteria_CFUs": 610000.0,
            "TNF_pg_ml": 498.3,
            "Viability_percent": 71.2
          },
          {
            "id": 3,
            "Condition": "TLR4 CRISPRi + loop donor",
            "Bacteria_CFUs": 940000.0,
            "TNF_pg_ml": 265.5,
            "Viability_percent": 83.6
          }
        ]
      }
    },
    "proteins": {
      "protein-tlr4-md2": {
        "name": "TLR4/MD-2 hybrid model",
        "description": "MD simulation (50 ns) suggests S325T/H431Y on TLR4 with MD-2 F121W stabilizes co-receptor interface.",
        "mutations": [
          "TLR4 S325T",
          "TLR4 H431Y",
          "MD-2 F121W"
        ],
        "predicted_ddG_kcal_mol": -3.2
      }
    },
    "protocols": {
      "protocol-donor-assembly": {
        "title": "TLR4 LRR14-18 donor assembly",
        "steps": [
          "Design donor with silent PAM shield (GAG>GAA) and S325T/H431Y substitutions.",
          "Assemble with Gibson (50 °C, 60 min) and verify by Sanger sequencing.",
          "Electroporate donor + Cas9 RNP into THP-1 CRISPRi clones; recover 48 h before challenge."
        ]
      }
    }
  },
  "snapshot": {
    "documentHtml": "<h1>Endotoxin Rescue Screen</h1><p>Hybrid edit (TLR4 S325T/H431Y + MD-2 F121W) predicted ddG −3.6 kcal/mol and improved bacterial clearance models.</p><p>Need wet-lab validation with NF-κB/IRF3 reporters.</p>",
    "sequenceBlocks": [
      {
        "id": "seq-tlr4-donor",
        "x": 90,
        "y": 228
      }
    ],
    "tables": {
      "table-killcurve": {
        "columns": [
          "Condition",
          "Bacteria_CFUs",
          "TNF_pg_ml",
          "Viability_percent"
        ],
        "rows": [
          {
            "id": 1,
            "Condition": "TLR4 CRISPRi",
            "Bacteria_CFUs": 2700000.0,
            "TNF_pg_ml": 186.0,
            "Viability_percent": 88.4
          },
          {
            "id": 2,
            "Condition": "NTC",
            "Bacteria_CFUs": 610000.0,
            "TNF_pg_ml": 498.3,
            "Viability_percent": 71.2
          },
          {
            "id": 3,
            "Condition": "TLR4 CRISPRi + loop donor",
            "Bacteria_CFUs": 940000.0,
            "TNF_pg_ml": 265.5,
            "Viability_percent": 83.6
          }
        ]
      }
    }
  }
}
