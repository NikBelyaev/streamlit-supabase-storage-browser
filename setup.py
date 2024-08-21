import setuptools

setuptools.setup(
    name="streamlit-supabase-storage-browser",
    version="1.0.0",
    author="",
    author_email="",
    description="",
    long_description="",
    long_description_content_type="text/plain",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.6",
    install_requires=[
        "pandas",
        "filetype",
        "streamlit-ace",
        "streamlit-molstar >= 0.4.6",
        "streamlit-antd",
        "streamlit-embeded",
        "streamlit >= 0.63",
        "pymatgen",
        "supabase",
    ],
)
