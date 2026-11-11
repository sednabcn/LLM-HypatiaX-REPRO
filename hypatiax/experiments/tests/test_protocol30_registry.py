import numpy as np

from hypatiax.protocols.experiment_protocol_benchmark_v2 import Protocol30


EXPECTED_DOMAINS = {
    "biology",
    "chemistry",
    "electrochemistry",
    "electromagnetism",
    "electrostatics",
    "magnetism",
    "mechanics",
    "optics",
    "probability",
    "quantum",
    "thermodynamics",
}


def test_protocol30_registry_has_manuscript_equation_and_domain_counts():
    protocol = Protocol30(num_samples=4, seed=42, noiseless=True)
    domains = protocol.get_all_domains()
    cases = [
        case
        for domain in domains
        for case in protocol.load_test_data(domain, num_samples=4)
    ]

    assert len(domains) == 11
    assert set(domains) == EXPECTED_DOMAINS
    assert len(cases) == 30
    assert len({case[4]["equation_name"] for case in cases}) == 30


def test_protocol30_data_are_analytic_noiseless_and_tagged_as_custom_protocol():
    protocol = Protocol30(num_samples=8, seed=42, noiseless=True)
    for domain in protocol.get_all_domains():
        for description, X, y, variable_names, metadata in protocol.load_test_data(
            domain, num_samples=8
        ):
            assert X.shape == (8, len(variable_names))
            assert y.shape == (8,)
            assert np.isfinite(X).all()
            assert np.isfinite(y).all()
            assert metadata["benchmark"] == "protocol30"
            assert metadata["protocol_id"] == Protocol30.protocol_id
            assert metadata["domain"] == domain
            assert metadata["registry_source"] == Protocol30.registry_source
            assert metadata["ground_truth"]
