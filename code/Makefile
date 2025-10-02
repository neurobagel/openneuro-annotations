all_data: openneuro_datasets.tsv openneuro_derivatives.tsv

openneuro_datasets.tsv:
	./find_openneuro.sh OpenNeuroDatasets ./open_neuro_datasets.tsv

openneuro_derivatives.tsv:
	./find_openneuro.sh OpenNeuroDerivatives ./open_neuro_derivatives.tsv

repo_map.json:
	python build_repo_map.py
