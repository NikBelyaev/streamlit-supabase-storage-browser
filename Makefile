build:
	cd streamlit_supabase_storage_browser/frontend && npm run build && cd ../..
	python setup.py sdist
