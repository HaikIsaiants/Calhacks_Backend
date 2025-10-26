#!/usr/bin/env python3
"""
Post a mock analysis payload to the backend, emulating a completed Letta run.

Usage:
    python send_mock_analysis.py --url http://localhost:8000
"""

import argparse
import json
import sys
from typing import Any, Dict

import httpx

# Paste the JSON payload between the triple quotes below.
PAYLOAD: Dict[str, Any] = json.loads(
    r"""
{
  "breakthrough_summary": {
    "text": "Computational modeling and functional assays demonstrate that dual modification of CFTR at positions F508 and R553 can restore NBD1 stability and enhance NBD1-NBD2 coupling, leading to improved chloride channel activity and cellular resistance to Pseudomonas aeruginosa challenge.",
    "source_ids": ["src-notebook", "src-archival-rabeh2012", "src-archival-hwang2009"]
  },
  "recommended_protein_edit": {
    "target_protein": {
      "text": "CFTR",
      "source_ids": ["src-notebook"]
    },
    "edit_type": {
      "text": "site-directed mutagenesis with dual substitutions",
      "source_ids": ["src-archival-rabeh2012"]
    },
    "edit_details": {
      "text": "Introduce F508S substitution to restore NBD1 surface stability combined with R553Q to optimize the NBD1-ICL4 interface and improve ATP coupling efficiency.",
      "source_ids": ["src-notebook", "src-archival-rabeh2012"]
    },
    "rationale": {
      "text": "F508 deletion is the most common CF mutation causing both thermodynamic and kinetic destabilization of NBD1. Research demonstrates that both NBD1 energetic stabilization and domain interface correction are required synergistically for rescue. The F508S mutation restores the critical NBD1 surface contact while R553Q enhances the ICL4 coupling interface, addressing both defects simultaneously.",
      "source_ids": ["src-archival-rabeh2012", "src-notebook"]
    }
  },
  "expected_outcome": {
    "text": "Increased chloride transport by 45-65% compared to ΔF508 mutant, with enhanced plasma membrane stability and significantly improved viability under Pseudomonas challenge (60-65% vs 35-40% for ΔF508 controls).",
    "source_ids": ["src-notebook", "src-archival-moreau2008"]
  },
  "confidence": 0.76,
  "next_steps": [
    {
      "text": "Validate F508S/R553Q double mutant stability using molecular dynamics simulations at physiological temperature.",
      "source_ids": ["src-archival-rabeh2012"]
    },
    {
      "text": "Generate mammalian expression constructs and confirm proper membrane trafficking via immunofluorescence.",
      "source_ids": ["src-notebook"]
    },
    {
      "text": "Conduct patch-clamp electrophysiology to measure single-channel open probability and ATP sensitivity.",
      "source_ids": ["src-archival-hwang2009", "src-notebook"]
    },
    {
      "text": "Perform extended Pseudomonas challenge assays to confirm improved bacterial clearance and sustained cell viability.",
      "source_ids": ["src-notebook", "src-archival-moreau2008"]
    }
  ],
  "analysis_summary": {
    "text": "The notebook data demonstrate robust functional improvements in NBD1→NBD2 coupling with enhanced chloride conductance and pathogen resistance. Cross-referencing with established CFTR structural biology reveals that ΔF508 causes dual defects: NBD1 energetic instability and impaired domain interfaces. The proposed F508S/R553Q strategy addresses both lesions simultaneously. Statistical analysis confirms significant viability gains (Welch t-test, p<0.001) and chloride current recovery (ANOVA, p<0.0001) compared to ΔF508 controls, approaching wild-type function. Bayesian integration with literature priors supports high confidence in the therapeutic potential of this dual-edit approach.",
    "source_ids": ["src-notebook", "src-archival-rabeh2012", "src-archival-hwang2009", "src-archival-moreau2008"]
  },
  "edited_protein": {
    "id": "ABCC7",
    "label": "CFTR",
    "description": {
      "text": "Cystic fibrosis transmembrane conductance regulator; ATP-gated chloride channel whose activity depends on PKA phosphorylation and proper NBD dimerization.",
      "source_ids": ["src-archival-hwang2009"]
    },
    "mutations": [
      {
        "text": "F508S: Serine substitution at position 508 to restore NBD1 folding stability and surface topology lost in ΔF508 mutation",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      },
      {
        "text": "R553Q: Glutamine substitution at position 553 to strengthen NBD1-ICL4 interface contacts and improve coupling to transmembrane domains",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      }
    ],
    "confidence": 0.76
  },
  "graph": {
    "nodes": [
      {
        "id": "P1",
        "label": "CFTR (Edited)",
        "type": "protein",
        "isEdited": true,
        "notes": "ATP-gated chloride channel with F508S/R553Q mutations targeting NBD1 stability and interface coupling.",
        "relationship_to_edited": "Edited target protein",
        "role_summary": "Dual mutations expected to restore folding, membrane trafficking, and ATP-driven gating to near wild-type levels.",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      },
      {
        "id": "E1",
        "label": "ATP",
        "type": "entity",
        "isEdited": false,
        "notes": "Adenosine triphosphate; required nucleotide substrate for CFTR gating.",
        "relationship_to_edited": "Essential cofactor",
        "role_summary": "Binding and hydrolysis at NBD sites drives channel opening and closing; improved NBD stability enhances ATP coupling efficiency.",
        "source_ids": ["src-archival-hwang2009", "src-notebook"]
      },
      {
        "id": "P2",
        "label": "NBD1",
        "type": "protein",
        "isEdited": false,
        "notes": "First nucleotide-binding domain containing the F508 position critical for folding and domain assembly.",
        "relationship_to_edited": "Directly stabilized by F508S mutation",
        "role_summary": "F508S mutation restores thermodynamic and kinetic stability, enabling proper heterodimerization with NBD2.",
        "source_ids": ["src-archival-rabeh2012", "src-notebook"]
      },
      {
        "id": "P3",
        "label": "NBD2",
        "type": "protein",
        "isEdited": false,
        "notes": "Second nucleotide-binding domain that heterodimerizes with NBD1 to form functional ATP-binding sites.",
        "relationship_to_edited": "Downstream binding partner",
        "role_summary": "Stabilized NBD1 promotes efficient NBD1-NBD2 heterodimerization required for ATP-driven gating.",
        "source_ids": ["src-archival-hwang2009", "src-notebook"]
      },
      {
        "id": "P4",
        "label": "ICL4",
        "type": "protein",
        "isEdited": false,
        "notes": "Intracellular loop 4; coupling helix connecting NBD1 to transmembrane domain 2.",
        "relationship_to_edited": "Interface strengthened by R553Q",
        "role_summary": "R553Q optimizes NBD1-ICL4 contacts, improving propagation of NBD conformational changes to the channel pore.",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      },
      {
        "id": "E2",
        "label": "Chloride",
        "type": "entity",
        "isEdited": false,
        "notes": "Chloride anion conducted through CFTR transmembrane pore.",
        "relationship_to_edited": "Transport substrate",
        "role_summary": "Enhanced chloride flux serves as primary functional readout; notebook data show recovery to 45-65% of wild-type current.",
        "source_ids": ["src-notebook"]
      },
      {
        "id": "P5",
        "label": "PKA",
        "type": "protein",
        "isEdited": false,
        "notes": "Protein kinase A; phosphorylates CFTR regulatory domain to enable channel activation.",
        "relationship_to_edited": "Upstream regulatory activator",
        "role_summary": "Notebook confirms phosphorylation-dependent activation remains intact in edited construct.",
        "source_ids": ["src-notebook", "src-archival-hwang2009"]
      },
      {
        "id": "E3",
        "label": "P. aeruginosa",
        "type": "entity",
        "isEdited": false,
        "notes": "Pseudomonas aeruginosa pathogen; major infectious agent in cystic fibrosis.",
        "relationship_to_edited": "Pathogen challenge agent",
        "role_summary": "Functional CFTR rescue improves bacterial clearance and cell viability during infection; notebook shows 60-65% viability vs 35-40% in ΔF508 controls.",
        "source_ids": ["src-notebook", "src-archival-moreau2008"]
      }
    ],
    "edges": [
      {
        "source": "E1",
        "target": "P2",
        "interaction": "binds",
        "mechanism": "ATP occupies the NBD1 binding pocket, stabilizing the closed NBD dimer conformation.",
        "explanation": "Restored NBD1 stability via F508S improves ATP binding affinity and dimer stability.",
        "source_ids": ["src-archival-hwang2009", "src-archival-rabeh2012"]
      },
      {
        "source": "E1",
        "target": "P3",
        "interaction": "binds and hydrolyzes",
        "mechanism": "ATP binding at NBD2 site triggers hydrolysis that drives the channel opening/closing cycle.",
        "explanation": "Improved NBD1-NBD2 coupling enhances hydrolysis-driven gating kinetics.",
        "source_ids": ["src-archival-hwang2009", "src-notebook"]
      },
      {
        "source": "P2",
        "target": "P3",
        "interaction": "heterodimerizes",
        "mechanism": "NBD1 and NBD2 form head-to-tail heterodimer with two composite ATP-binding sites at the dimer interface.",
        "explanation": "F508S stabilization enables proper NBD1-NBD2 interface formation required for functional gating.",
        "source_ids": ["src-archival-rabeh2012", "src-archival-hwang2009"]
      },
      {
        "source": "P2",
        "target": "P4",
        "interaction": "couples to",
        "mechanism": "NBD1 contacts ICL4 (intracellular loop 4) to transmit conformational changes to transmembrane domains.",
        "explanation": "R553Q strengthens the NBD1-ICL4 interface, improving mechanical coupling and gating efficiency.",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      },
      {
        "source": "P2",
        "target": "P1",
        "interaction": "regulates",
        "mechanism": "NBD1 conformational changes propagate through coupling helices to gate the transmembrane pore.",
        "explanation": "Dual mutations reduce NBD1 misfolding, allowing proper signal transmission to the pore domain.",
        "source_ids": ["src-archival-rabeh2012", "src-notebook"]
      },
      {
        "source": "P3",
        "target": "P1",
        "interaction": "regulates",
        "mechanism": "NBD2 ATP hydrolysis drives the channel closing phase of the gating cycle.",
        "explanation": "Enhanced NBD1-NBD2 coupling maintains proper hydrolysis-driven kinetics observed in current recordings.",
        "source_ids": ["src-archival-hwang2009", "src-notebook"]
      },
      {
        "source": "P4",
        "target": "P1",
        "interaction": "couples to",
        "mechanism": "ICL4 mechanically links NBD1 to transmembrane domain 2, propagating NBD motions to the pore.",
        "explanation": "Optimized NBD1-ICL4 contact via R553Q improves transmission of ATP-driven conformational changes.",
        "source_ids": ["src-notebook", "src-archival-rabeh2012"]
      },
      {
        "source": "P1",
        "target": "E2",
        "interaction": "transports",
        "mechanism": "Chloride ions permeate through the CFTR transmembrane pore when the channel is in the open state.",
        "explanation": "Notebook data show 45-65% recovery of wild-type chloride current, indicating restored transport function.",
        "source_ids": ["src-notebook"]
      },
      {
        "source": "P5",
        "target": "P1",
        "interaction": "activates",
        "mechanism": "PKA phosphorylates the CFTR regulatory (R) domain, relieving autoinhibition and enabling ATP-dependent gating.",
        "explanation": "Notebook confirms that phosphorylation-dependent activation is preserved in the edited construct.",
        "source_ids": ["src-notebook", "src-archival-hwang2009"]
      },
      {
        "source": "P1",
        "target": "E3",
        "interaction": "confers resistance to",
        "mechanism": "Functional CFTR at the plasma membrane improves bacterial clearance and reduces biofilm formation.",
        "explanation": "Rescued CFTR function significantly improves cell viability under Pseudomonas challenge (60-65% vs 35-40% for ΔF508).",
        "source_ids": ["src-notebook", "src-archival-moreau2008"]
      }
    ]
  },
  "statistical_analysis": {
    "summary": "Welch t-test demonstrates that the F508S/R553Q edited CFTR significantly enhances cell viability during Pseudomonas challenge compared to ΔF508 controls (p<0.001, Cohen's d=5.14). One-way Welch ANOVA confirms that the edited construct restores chloride conductance to an intermediate level between ΔF508 and wild-type (p<0.0001), with post-hoc tests showing the edited variant achieves 68% of wild-type current while significantly exceeding ΔF508 baseline. Bayesian integration with ABC transporter literature priors yields a posterior mean effect size of 0.74 with 95% HPD [0.56, 0.89], supporting the 0.76 confidence score.",
    "data_sources": [
      {
        "name": "Notebook: Pseudomonas Challenge Viability Assay",
        "description": "Percent viable cells measured 24 hours after exposure to Pseudomonas aeruginosa.",
        "conditions": [
          "ΔF508 control",
          "ΔF508 + CFTR F508S/R553Q",
          "Wild-type CFTR"
        ],
        "replicates_per_condition": 6
      },
      {
        "name": "Notebook: Short-Circuit Current Measurements",
        "description": "Chloride current density (µA/cm²) from Ussing chamber recordings of polarized epithelial monolayers.",
        "replicates_per_condition": 6
      },
      {
        "name": "External: ABC Transporter Domain Interface Studies",
        "description": "Meta-analysis of NBD stabilizing mutations across ABC transporter superfamily used as Bayesian prior.",
        "url": "https://www.sciencedirect.com/science/article/pii/S0092867411013687",
        "pmid": "22265408"
      }
    ],
    "tests": [
      {
        "test_name": "Welch t-test",
        "comparison": "ΔF508 + CFTR F508S/R553Q vs ΔF508 control",
        "metric": "Cell viability (%) after Pseudomonas challenge",
        "sample_sizes": {
          "edited": 6,
          "control": 6
        },
        "group_means": {
          "edited": 63.4,
          "control": 37.8
        },
        "group_std": {
          "edited": 2.8,
          "control": 3.2
        },
        "statistic": 16.32,
        "degrees_of_freedom": 9.8,
        "p_value": 0.00008,
        "effect_size_cohens_d": 5.14,
        "confidence_interval_95": {
          "lower": 21.2,
          "upper": 30.0,
          "units": "percentage points"
        },
        "assumptions_check": "Shapiro-Wilk test confirms normality in both groups (p>0.15). Levene test shows unequal variances (p=0.04), justifying Welch correction.",
        "interpretation": "The edited CFTR construct produces a 25.6 ± 4.4 percentage point improvement in viability over ΔF508 controls (p<0.001), with a very large effect size (Cohen's d=5.14), strongly supporting functional rescue.",
        "source_ids": ["src-notebook"]
      },
      {
        "test_name": "One-way Welch ANOVA",
        "comparison": "Wild-type CFTR, ΔF508 control, ΔF508 + CFTR F508S/R553Q",
        "metric": "Short-circuit current (µA/cm²)",
        "sample_sizes": {
          "wild_type": 6,
          "delta_f508": 6,
          "edited": 6
        },
        "group_means": {
          "wild_type": 44.8,
          "delta_f508": 10.4,
          "edited": 30.5
        },
        "welch_f": 72.6,
        "p_value": 0.00001,
        "post_hoc": [
          {
            "comparison": "Edited vs ΔF508",
            "method": "Games-Howell",
            "p_value": 0.00009,
            "mean_difference": 20.1,
            "units": "µA/cm²"
          },
          {
            "comparison": "Edited vs Wild-type",
            "method": "Games-Howell",
            "p_value": 0.012,
            "mean_difference": -14.3,
            "units": "µA/cm²"
          },
          {
            "comparison": "Wild-type vs ΔF508",
            "method": "Games-Howell",
            "p_value": 0.00007,
            "mean_difference": 34.4,
            "units": "µA/cm²"
          }
        ],
        "effect_size_partial_omega_squared": 0.82,
        "interpretation": "The edited channel recovers 68% of wild-type chloride current [(30.5-10.4)/(44.8-10.4)=0.58 baseline-adjusted, or 30.5/44.8=0.68 raw], significantly exceeding ΔF508 while remaining below wild-type. Large effect size (partial ω²=0.82) indicates the mutations account for most variance in conductance.",
        "source_ids": ["src-notebook"]
      },
      {
        "test_name": "Bayesian integration",
        "comparison": "Posterior probability distribution for functional rescue effect size",
        "prior": "Normal(μ=0.42, σ=0.14) derived from Rabeh et al. 2012 data on NBD1 stabilization and domain interface corrections in ABC transporters",
        "likelihood": "Observed effect from notebook data: Cohen's d=5.14 with SE=0.52 (converted to standardized effect metric)",
        "posterior_mean": 0.74,
        "posterior_hpd_95": [
          0.56,
          0.89
        ],
        "interpretation": "Bayesian updating with literature priors on NBD interface stabilization yields posterior mean effect of 0.74, indicating high credibility for substantial functional rescue. The 95% highest posterior density interval [0.56, 0.89] excludes small effects and supports the assigned confidence of 0.76.",
        "source_ids": ["src-archival-rabeh2012", "src-notebook"]
      }
    ],
    "data_used": {
      "pseudomonas_viability_percent": {
        "delta_f508_control": [35.2, 39.8, 36.4, 40.1, 38.5, 36.8],
        "edited_cftr": [61.8, 65.3, 62.9, 64.8, 63.1, 62.5],
        "wild_type": [69.5, 72.1, 70.8, 71.4, 68.9, 71.2]
      },
      "short_circuit_current_uA_cm2": {
        "wild_type": [45.2, 43.8, 46.1, 44.5, 43.9, 45.3],
        "delta_f508": [11.2, 10.8, 9.5, 10.1, 11.0, 9.8],
        "edited_cftr": [29.8, 31.5, 30.2, 31.8, 30.1, 29.6]
      },
      "notebook_metadata": {
        "experiment_id": "notebook-demo-3-2025-10-26",
        "analysis_timestamp": "2025-10-26T13:20:24Z"
      }
    }
  },
  "visualizations": [
    {
      "id": "viability_bar",
      "title": "Cell Viability After 24h Pseudomonas Challenge",
      "type": "bar_with_error",
      "x_labels": ["ΔF508 Control", "Edited CFTR (F508S/R553Q)", "Wild-type"],
      "values": [37.8, 63.4, 70.6],
      "error_bars": [3.2, 2.8, 1.8],
      "y_axis_label": "Viability (%)",
      "description": "Mean ± SD cell viability across six replicates per condition. Edited CFTR shows significant rescue compared to ΔF508 control (p<0.001).",
      "source_ids": ["src-notebook"]
    },
    {
      "id": "effect_size_intervals",
      "title": "Effect Sizes with 95% Confidence/Credible Intervals",
      "type": "interval_plot",
      "metrics": [
        {
          "label": "Viability Rescue (Cohen's d)",
          "point": 5.14,
          "ci_lower": 4.22,
          "ci_upper": 6.06
        },
        {
          "label": "Current Recovery (Partial ω²)",
          "point": 0.82,
          "ci_lower": 0.71,
          "ci_upper": 0.89
        },
        {
          "label": "Bayesian Posterior Effect",
          "point": 0.74,
          "ci_lower": 0.56,
          "ci_upper": 0.89
        }
      ],
      "x_axis_label": "Effect Magnitude",
      "description": "Comparison of statistical effect sizes from viability and conductance assays with Bayesian posterior credibility interval. All metrics support robust functional rescue.",
      "source_ids": ["src-notebook", "src-archival-rabeh2012"]
    }
  ],
  "sources": [
    {
      "id": "src-notebook",
      "name": "Notebook – CFTR Rescue Study Demo",
      "summary": "Functional rescue data for CFTR with emphasis on NBD1→NBD2 coupling, including viability under Pseudomonas challenge and short-circuit current measurements."
    },
    {
      "id": "src-archival-rabeh2012",
      "name": "Rabeh et al., Cell 2012",
      "url": "https://www.sciencedirect.com/science/article/pii/S0092867411013687",
      "summary": "Demonstrates that both NBD1 energetic stabilization and NBD1-MSD2 interface correction are required synergistically for ΔF508 CFTR rescue; informs mutation strategy and Bayesian prior."
    },
    {
      "id": "src-archival-hwang2009",
      "name": "Hwang & Kirk, J Physiol 2009",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2697289/",
      "summary": "Describes ATP-driven gating mechanism via NBD dimerization; explains how improved NBD1-NBD2 coupling enhances channel function."
    },
    {
      "id": "src-archival-moreau2008",
      "name": "Moreau-Marquis et al., Am J Physiol 2008",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2494796/",
      "summary": "Documents how ΔF508-CFTR mutation increases Pseudomonas biofilm formation and reduces cell viability; supports pathogen challenge readout."
    }
  ]
}    """
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send mock analysis payload to backend."
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the backend (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    endpoint = args.url.rstrip("/") + "/api/analysis/result"

    try:
        response = httpx.post(endpoint, json=PAYLOAD, timeout=60)
        response.raise_for_status()
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        if isinstance(exc, httpx.HTTPStatusError):
            print(f"Response body: {exc.response.text}", file=sys.stderr)
        sys.exit(1)

    print("POST succeeded.")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


if __name__ == "__main__":
    main()
