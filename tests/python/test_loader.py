"""Smoke tests for dataset loading + schema validation."""
from rclea_core import load_dataset


def test_dataset_loads() -> None:
    ds = load_dataset()
    # At least the original RCLEA catalogue of 47 isotopes; extensions are allowed.
    assert len(ds.isotopes) >= 47
    assert "Cs-137" in ds.isotopes
    assert "Ra-226" in ds.isotopes
    assert "Pu-239" in ds.isotopes


def test_scenarios_present() -> None:
    ds = load_dataset()
    expected = {
        "Residential_with_Home_Grown_Produce",
        "Residential_without_Home_Grown_Produce",
        "Allotments",
        "Commercial_Industrial",
    }
    assert expected.issubset(set(ds.scenarios))


def test_dose_criteria() -> None:
    ds = load_dataset()
    assert ds.constants.effective_dose_criterion_mSv_per_y == 3.0
    assert ds.constants.equivalent_skin_dose_criterion_mSv_per_y == 50.0


def test_cs137_adult_ingestion_dcf() -> None:
    """Published ICRP value for Cs-137 adult ingestion is 1.3e-8 Sv/Bq."""
    ds = load_dataset()
    cs = ds.isotopes["Cs-137"]
    assert cs.ingestion_Sv_per_Bq["adult"] == 1.3e-8
    assert cs.ingestion_Sv_per_Bq["child"] == 1.0e-8
    assert cs.ingestion_Sv_per_Bq["infant"] == 1.2e-8


def test_ra226_adult_inhalation_dcf() -> None:
    ds = load_dataset()
    ra = ds.isotopes["Ra-226"]
    assert ra.inhalation_Sv_per_Bq["adult"] == 3.5e-6
