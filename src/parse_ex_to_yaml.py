import pandas as pd
import yaml
from constants import LOCAL_DIRECTORY_YAML
import os


def parse_ex_to_yaml(LOCAL_DIRECTORY_YAML, template_excel):
    """
    Function that parse the metadata template that the user uploads in step 4 and creates a yaml file
    per sheet in the excel

    inputs:
        - LOCAL_DIRECTORY: path were the yaml files are going to be saved
        - template_excel: matadata excel file uploaded by the user

    Returns:
        - yaml file per sheet in metadata excel: STUDY.yaml, EXPERIMENTS.yaml, COMPARTMENTS.yaml,
        COMMUNITY_MEMBERS.yaml, COMMUNITIES.yaml, PERTURBATIONS.yaml
    """

    # Read the completed Excel file
    df_excel_1 = pd.read_excel(template_excel, engine='openpyxl',sheet_name='STUDY')
    df_excel_2 = pd.read_excel(template_excel, engine='openpyxl' ,sheet_name='EXPERIMENTS')
    df_excel_3 = pd.read_excel(template_excel, engine='openpyxl',sheet_name='COMPARTMENTS')
    df_excel_4 = pd.read_excel(template_excel, engine='openpyxl',sheet_name='COMMUNITY_MEMBERS')
    df_excel_5 = pd.read_excel(template_excel, engine='openpyxl',sheet_name='COMMUNITIES')
    df_excel_6 = pd.read_excel(template_excel, engine='openpyxl',sheet_name='PERTURBATIONS')

    # Convert start_time and end_time to strings
    df_excel_6['Perturbation_StartTime'] = df_excel_6['Perturbation_StartTime'].astype(str)
    df_excel_6['Perturbation_EndTime'] = df_excel_6['Perturbation_EndTime'].astype(str)


    # Initialize dictionaries for each prefix
    data_dicts = {}

    data_dicts = {col: df_excel_1[col].tolist() for col in df_excel_1.columns}


    data_dicts2 = {}
    data_dicts2 = {col: df_excel_2[col].tolist() for col in df_excel_2.columns}

    data_dicts3 = {}
    data_dicts3 = {col: df_excel_3[col].tolist() for col in df_excel_3.columns}


    data_dicts4 = {}
    data_dicts4 = {col: df_excel_4[col].tolist() for col in df_excel_4.columns}

    data_dicts5 = {}
    data_dicts5 = {col: df_excel_5[col].tolist() for col in df_excel_5.columns}

    data_dicts6 = {}
    data_dicts6 = {col: df_excel_6[col].tolist() for col in df_excel_6.columns}
    # Convert DataFrame to YAML
    yaml_data = yaml.dump(data_dicts)
    yaml_data2 = yaml.dump(data_dicts2)
    yaml_data3 = yaml.dump(data_dicts3)
    yaml_data4 = yaml.dump(data_dicts4)
    yaml_data5 = yaml.dump(data_dicts5)
    yaml_data6 = yaml.dump(data_dicts6)


    template_filename_yaml_STUDY = os.path.join(LOCAL_DIRECTORY_YAML, 'STUDY.yaml')
    template_filename_yaml_EXPERIMENTS = os.path.join(LOCAL_DIRECTORY_YAML, 'EXPERIMENTS.yaml')
    template_filename_yaml_COMPARTMENTS = os.path.join(LOCAL_DIRECTORY_YAML, 'COMPARTMENTS.yaml')
    template_filename_yaml_COMMUNITY_MEMBERS = os.path.join(LOCAL_DIRECTORY_YAML, 'COMMUNITY_MEMBERS.yaml')
    template_filename_yaml_COMMUNITIES = os.path.join(LOCAL_DIRECTORY_YAML, 'COMMUNITIES.yaml')
    template_filename_yaml_PERTURBATIONS = os.path.join(LOCAL_DIRECTORY_YAML, 'PERTURBATIONS.yaml')

    all_yamls = [template_filename_yaml_STUDY, template_filename_yaml_EXPERIMENTS, template_filename_yaml_COMPARTMENTS,
                 template_filename_yaml_COMMUNITY_MEMBERS, template_filename_yaml_COMMUNITIES, template_filename_yaml_PERTURBATIONS]
    for yamlfile in all_yamls:
        if os.path.isfile(yamlfile):
            os.remove(yamlfile)
    print("\n\n\n\n\n  tmp yamls")
    print(os.listdir(LOCAL_DIRECTORY_YAML))


    # Write YAML data to a file
    with open(template_filename_yaml_STUDY, "w") as yaml_file:
        yaml_file.write(yaml_data)

    # Write YAML data to a file
    with open(template_filename_yaml_EXPERIMENTS, "w") as yaml_file:
        yaml_file.write(yaml_data2)

    # Write YAML data to a file
    with open(template_filename_yaml_COMPARTMENTS, "w") as yaml_file:
        yaml_file.write(yaml_data3)

    with open(template_filename_yaml_COMMUNITY_MEMBERS, "w") as yaml_file:
        yaml_file.write(yaml_data4)

    with open(template_filename_yaml_COMMUNITIES, "w") as yaml_file:
        yaml_file.write(yaml_data5)

    with open(template_filename_yaml_PERTURBATIONS, "w") as yaml_file:
        yaml_file.write(yaml_data6)


