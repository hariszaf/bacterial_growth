import os
import uuid
import pandas as pd

import itertools

import flask_app.legacy.db_functions as db
from flask_app.legacy.yml_functions import read_yml
from flask_app.legacy.parse_raw_data import get_techniques_metabolites, get_measures_growth, get_measures_reads, get_measures_counts, get_replicate_metadata

# TODO Temporary:
root_folder = os.path.abspath(os.path.dirname(__file__) + '/../../')

LOCAL_DIRECTORY           = os.path.join(root_folder, "")
LOCAL_DIRECTORY_APP       = os.path.join(LOCAL_DIRECTORY, "app")
LOCAL_DIRECTORY_TEMPLATES = os.path.join(LOCAL_DIRECTORY_APP, "templates")
LOCAL_DIRECTORY_YAML      = os.path.join(LOCAL_DIRECTORY_TEMPLATES, "yaml_templates")

class GrowthTechniques:
    def __init__(self):
        self.od = "Optical Density"
        self.plates = "Plate Counts"
        self.plates_ps = "Plate Counts (per species)"
        self.fc = "Flow Cytometry"
        self.fc_ps = "Flow Cytometry (per species)"
        self.rna = "16S rRNA-seq"

class Vessels:
    def __init__(self):
        # 'Bottles', 'Agar-plates', 'Well-plates', 'mini-bioreactors'
        self.bottles = "Bottles"
        self.agar_plates = "Agar plates"
        self.well_plates = "Well plates"
        self.mini_react = "mini bioreactors"

def save_submission_to_database(conn, submission, data_template):
    """
    Function that populates all the data from the yaml files if not errors, in case of errors the function stops and returns the error

    inputs:
        - conn:          a database connection
        - submission:    a dict with submission details
        - data_template: an excel file uploaded by the user in step 4 with all the raw data

    Returns:
        - study_id:                 study id of the uploaded study if susccessfull, if not it will be None
        - errors:                   List of all the errors resulting from the get_techniques_metabolites function
        - errors_logic:             List of all logial errors checked while populating the data into the database
        - study['studyUniqueID']:   Study Unique ID only if all was susscessful
        - study['projectUniqueID']: Project Unique ID only if all was susscessful
    """
    # TODO (2024-10-20) Taken directly from streamlit app, so we just rename the fields for now:
    list_growth = [submission.technique_type]
    list_metabolites = [name for (cheb_id, name) in submission.fetch_metabolites()]

    list_microbial_strains = [name for (id, name) in submission.fetch_strains()]
    list_microbial_strains += [strain['name'] for strain in submission.fetch_new_strains()]

    info_file_study       = os.path.join(LOCAL_DIRECTORY_YAML, 'STUDY.yaml')
    info_file_experiments = os.path.join(LOCAL_DIRECTORY_YAML, 'EXPERIMENTS.yaml')
    info_compart_file     = os.path.join(LOCAL_DIRECTORY_YAML, 'COMPARTMENTS.yaml')
    info_mem_file         = os.path.join(LOCAL_DIRECTORY_YAML, 'COMMUNITY_MEMBERS.yaml')
    info_comu_file        = os.path.join(LOCAL_DIRECTORY_YAML, 'COMMUNITIES.yaml')
    info_pert_file        = os.path.join(LOCAL_DIRECTORY_YAML, 'PERTURBATIONS.yaml')

    # checks that all the options selected by the user in the interface match the uploaded raw data template
    errors = get_techniques_metabolites(list_growth, list_metabolites,list_microbial_strains, data_template)
    errors_logic = []

    study_id = None
    project_id = None

    if not errors:
        #defining the dictioraries depending on the raw data uploaded by the user
        measures, metabos = get_measures_growth(data_template)
        abundances_per_replicate = get_measures_reads(data_template)
        counts_per_replicate = get_measures_counts(data_template)
        replicate_metadata = get_replicate_metadata(data_template)

        #reads all the yaml file
        info_study = read_yml(info_file_study)
        info = read_yml(info_file_experiments)
        info_compart = read_yml(info_compart_file)
        info_pertu = read_yml(info_pert_file)
        info_mem = read_yml(info_mem_file)
        info_comu = read_yml(info_comu_file)

        #defining dictionaries per every yaml file
        study_name_list = info_study['Study_Name']
        experiment_name_list = info['Experiment_ID']
        #defining the number of rows with information in every yaml
        num_experiment = len(experiment_name_list)
        num_compart = len(info_compart['Compartment_ID'])
        num_pertu = len(info_pertu['Perturbation_ID'])
        num_mem = len(info_mem['Member_ID'])
        num_comu = len(info_comu['Community_ID'])
        num_rep_metadata = len(replicate_metadata['Biological_Replicate_id'])

        #populating the study table
        if 'Study_Name' in info_study:
            study = {
                'studyId' : db.getStudyID(conn),
                'studyName': info_study['Study_Name'][0],
                'studyDescription': info_study['Study_Description'][0],
                'studyURL': info_study['Study_PublicationURL'][0],
                'studyUniqueID': info_study['Study_UniqueID'][0],
                'projectUniqueID':  info_study['Project_UniqueID'][0]
                }
            if isinstance(info_study['Study_UniqueID'][0], float) :
                study['studyUniqueID'] = str(uuid.uuid4())

            study_filtered = {k: v for k, v in study.items() if v is not None}

            if len(study_filtered)>0:
                print(study_filtered)
                study_id = db.addRecord('Study', study_filtered)

            else:
                print('You must introduce some study information')
                exit()

        if 'Project_UniqueID' in info_study:

            project = {
                'projectId' : db.getProjectID(conn),
                'projectName': submission.project['name'],
                'projectDescription': submission.project['description'],
                'projectUniqueID': info_study['Project_UniqueID'][0]
            }

            project_filtered = {k: v for k, v in project.items() if v is not None}

            if len(project_filtered)>0:
                    project_id = db.addRecord('Project', project_filtered)
                    print('\nProject ID: ', project_id)
            else:
                print('You must introduce some study information')
                exit()

        #defining list that will save all the names and their corresponding ids
        biorep_id_list = []
        rep_id_list = []
        compartments_id_list = []
        mem_id_list =[]
        mem_name_id_list = []
        comu_id_list =[]

        # populating strains table
        if 'Member_ID' in info_mem:
            for i in range(num_mem):
                mem_id = info_mem['Member_ID'][i]
                members = {
                    'studyId': study_id,
                    'memberId' : info_mem['Member_ID'][i],
                    'defined': info_mem['Defined'][i],
                    'memberName': info_mem['Member_Name'][i],
                    'NCBId': info_mem['NCBI_ID'][i],
                    'descriptionMember': info_mem['Description'][i]
                    }
                members_filtered = {k: v for k, v in members.items() if v is not None}
                if len(members_filtered)>0:
                    members_id = db.addRecord('Strains', members_filtered)
                    mem_id_list.append((mem_id,members_id))
                    mem_name_id_list.append((info_mem['Member_Name'][i],mem_id))
                    print('\n MEMBER UNIQUE ID: ', members_id)
                else:
                    print('You must introduce some study information')
                    exit()

        # populating compartments table
        if 'Compartment_ID' in info_compart:
            for i in range(num_compart):
                compartments = {
                    'studyId': study_id,
                    'compartmentId' : info_compart['Compartment_ID'][i],
                    'volume' : info_compart['Compartment_Volume'][i],
                    'pressure': info_compart['Compartment_Pressure'][i],
                    'stirring_speed': info_compart['Compartment_StirringSpeed'][i],
                    'stirring_mode': info_compart['Compartment_StirringMode'][i],
                    'O2': info_compart['O2%'][i],
                    'CO2': info_compart['CO2%'][i],
                    'H2': info_compart['H2%'][i],
                    'N2': info_compart['N2%'][i],
                    'inoculumConcentration': info_compart['Inoculum_Concentration'][i],
                    'inoculumVolume': info_compart['Inoculum_Volume'][i],
                    'initialPh': info_compart['Initial_pH'][i],
                    'initialTemperature': info_compart['Initial_Temperature'][i],
                    'carbonSource': info_compart['Carbon_Source'][i],
                    'mediaNames': info_compart['Medium_Name'][i],
                    'mediaLink': info_compart['Medium_Link'][i]
                    }
                compartments_filtered = {k: v for k, v in compartments.items() if v is not None}
                if len(compartments_filtered)>0:
                    compartments_id = db.addRecord('Compartments', compartments_filtered)
                    compartments_id_list.append((info_compart['Compartment_ID'][i], compartments_id))
                    print('\n COMPARTMENTS UNIQUE ID: ', compartments_id)
                else:
                    print('You must introduce some study information')
                    exit()

        # populating experiments table
        if 'Experiment_ID' in info:
            for i in range(num_experiment):
                biologicalreplicates = {
                    'experimentId': info['Experiment_ID'][i],
                    'studyId': study_id,
                    'experimentDescription': info['Experiment_Description'][i],
                    'cultivationMode': info['Cultivation_Mode'][i],
                    'controlDescription': info['Control_Description'][i]
                }
                biologicalreplicates_filtered = {k: v for k, v in biologicalreplicates.items() if v is not None}
                if len(biologicalreplicates_filtered)>0:
                    biologicalReplicate_id = db.addRecord('Experiments', biologicalreplicates_filtered)
                    biorep_id_list.append((info['Experiment_ID'][i],biologicalReplicate_id))
                    print('\nEXPERIMENT ID: ', biologicalReplicate_id)
                else:
                    print('You must introduce some study information')
                    exit()

        #populating Community table
        if 'Community_ID' in info_comu:
            for i in range(num_comu):
                member = stripping_method(info_comu['Member_ID'][i])
                for j in member:
                    strain_id = search_id(j,mem_id_list)
                    if strain_id == None:
                        error_ms  = 'Member_ID in COMMUNITIES sheet is not defined in COMMUNITY_MEMBERS. Please check!'
                        errors_logic.append(error_ms)
                    comunities = {
                        'studyId': study_id,
                        'comunityId': info_comu['Community_ID'][i],
                        'strainId': strain_id
                    }
                    comunities_filtered = {k: v for k, v in comunities.items() if v is not None}
                    if len(comunities_filtered)>0:
                        comunities_id = db.addRecord('Community', comunities_filtered)
                        comu_id_list.append((info_comu['Community_ID'][i],comunities_id))
                        print('\nCOMUNITY UNIQUE ID: ', comunities_id)
                    else:
                        print('You must introduce some study information')
                        exit()

        #populating perturbations table
        if 'Perturbation_ID' in info_pertu:
            for i in range(num_pertu):
                biological_id_spec =  search_id(info_pertu['Experiment_ID'][i],biorep_id_list)
                if biological_id_spec == None:
                    error_ms  = f"Experiment_ID {info_pertu['Experiment_ID'][i]} in PERTURBATIONS sheet is not defined in EXPERIMENTS. Please check!"
                    errors_logic.append(error_ms)
                if not isinstance(info_pertu['OLD_Compartment_ID'][i], float)  and  (info_pertu['OLD_Compartment_ID'][i] not in info_compart['Compartment_ID']):
                    error_ms = f"OLD_Compartment_ID {info_pertu['OLD_Compartment_ID'][i]} in PERTURBATIONS sheet is not defined in COMPARTMENTS. Please check!"
                    errors_logic.append(error_ms)
                if not isinstance(info_pertu['NEW_Compartment_ID'][i], float) and (info_pertu['NEW_Compartment_ID'][i] not in info_compart['Compartment_ID']):
                    error_ms = f"NEW_Compartment_ID {info_pertu['NEW_Compartment_ID'][i]} in PERTURBATIONS sheet is not defined in COMPARTMENTS. Please check!"
                    errors_logic.append(error_ms)
                if not isinstance(info_pertu['OLD_Community_ID'][i], float) and info_pertu['OLD_Community_ID'][i] not in info_comu['Community_ID']:
                    error_ms = f"OLD_Community_ID {info_pertu['OLD_Community_ID'][i]} in PERTURBATIONS sheet is not defined in COMMUNITITES. Please check!"
                    errors_logic.append(error_ms)
                if not isinstance(info_pertu['NEW_Community_ID'][i], float) and (info_pertu['NEW_Community_ID'][i] not in info_comu['Community_ID']):
                    error_ms = f"NEW_Community_ID {info_pertu['NEW_Community_ID'][i]} in PERTURBATIONS sheet is not defined in COMMUNITITES. Please check!"
                    errors_logic.append(error_ms)
                perturbations = {
                    'studyId': study_id,
                    'perturbationId': info_pertu['Perturbation_ID'][i],
                    'experimentUniqueId': biological_id_spec,
                    'experimentId': info_pertu['Experiment_ID'][i],
                    'OLDCompartmentId': info_pertu['OLD_Compartment_ID'][i],
                    'OLDComunityId': info_pertu['OLD_Community_ID'][i],
                    'NEWCompartmentId': info_pertu['NEW_Compartment_ID'][i],
                    'NEWComunityId': info_pertu['NEW_Community_ID'][i],
                    'perturbationDescription': info_pertu['Perturbation_Description'][i],
                    'perturbationMinimumValue': info_pertu['Perturbation_MinimumValue'][i],
                    'perturbationMaximumValue': info_pertu['Perturbation_MaximumValue'][i],
                    'perturbationStartTime': datetime.strptime(info_pertu['Perturbation_StartTime'][i], '%H:%M:%S').time(),
                    'perturbationEndTime': datetime.strptime(info_pertu['Perturbation_EndTime'][i], '%H:%M:%S').time()
                    }
                perturbation_filtered = {k: v for k, v in perturbations.items() if v is not None}
                if len(perturbation_filtered)>0:
                    perturbation_id=db.addRecord('Perturbation', perturbation_filtered)

        if 'Experiment_ID' in info:
            for i in range(num_experiment):
                comp_biorep = stripping_method(info['Compartment_ID'][i])
                comu_biorep = stripping_method(info['Community_ID'][i])
                for j,k in zip(comp_biorep, itertools.cycle(comu_biorep)):
                    comp_per_biorep={
                        'studyId': study_id,
                        'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                        'experimentId': info['Experiment_ID'][i],
                        'compartmentUniqueId': search_id(j, compartments_id_list),
                        'compartmentId': j,
                        'comunityUniqueId': search_id(k,comu_id_list),
                        'comunityId': k
                    }
                    comp_per_biorep_filtered = {t: v for t, v in comp_per_biorep.items() if v is not None}
                    if len(comp_per_biorep_filtered)>0:
                        db.addRecord('CompartmentsPerExperiment', comp_per_biorep_filtered)
                tech_biorep = stripping_method(info['Measurement_Technique'][i])
                unit_biorep = stripping_method(info['Measurement_Technique'][i])
                if len(tech_biorep) != len(unit_biorep):
                    error_ms = 'Measurement_Technique and Measurement_Technique must have the same number of entries per celd.'
                    error_ms.append(error_ms)

                for j, k in zip(tech_biorep, unit_biorep):
                    tech_per_biorep={
                        'studyId': study_id,
                        'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                        'experimentId': info['Experiment_ID'][i],
                        'technique': j,
                        'techniqueUnit': k
                    }
                    tech_per_biorep_filtered = {k: v for k, v in tech_per_biorep.items() if v is not None}
                    if len(tech_per_biorep_filtered)>0:
                        db.addRecord('TechniquesPerExperiment', tech_per_biorep_filtered)

                rep_biorep = stripping_method(info['Biological_Replicate_IDs'][i])
                rep_controls = stripping_method(str(info['Control'][i]))
                for j in range(len(rep_biorep)):
                    list_measures = measures.get(rep_biorep[j])

                    if not list_measures:
                        error_ms = f"Biological_Replicate_ID: {rep_biorep[j]} was not defined in the raw data template excel. Please correct!"
                        errors_logic.append(error_ms)

                    elif list_measures:
                        control = 0
                        od = 0
                        od_std = 0
                        platecounts = 0
                        platecounts_std = 0
                        ph = 0
                        if rep_biorep[j] in rep_controls:
                            control = 1
                        if 'OD' in list_measures:
                            od = 1
                        if 'OD_std' in list_measures:
                            od_std = 1
                        if 'Plate_counts' in list_measures:
                            platecounts = 1
                        if 'Plate_counts_std' in list_measures:
                            platecounts_std = 1
                        if 'pH' in list_measures:
                            ph = 1
                        rep_per_biorep = {
                            'studyId' : study_id,
                            'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                            'experimentId': info['Experiment_ID'][i],
                            'bioreplicateId': rep_biorep[j],
                            'controls': control,
                            'OD': od,
                            'OD_std': od_std,
                            'Plate_counts': platecounts,
                            'Plate_counts_std': platecounts_std,
                            'pH': ph,
                        }
                        rep_per_biorep_filtered = {k: v for k, v in rep_per_biorep.items() if v is not None}
                        if len(rep_per_biorep_filtered)>0:
                            rep_id = db.addRecord('BioReplicatesPerExperiment', rep_per_biorep_filtered)
                            rep_id_list.append((rep_biorep[j],rep_id))

                for j in range(len(rep_biorep)):
                    list_metabo = metabos.get(rep_biorep[j])
                    list_abundances = abundances_per_replicate.get(rep_biorep[j])
                    list_counts = counts_per_replicate.get(rep_biorep[j])
                    if list_metabo:
                        for k in list_metabo:
                            cheb_id = db.getChebiId(k)
                            metabo_rep = {
                                'studyId': study_id,
                                'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                                'experimentId': info['Experiment_ID'][i],
                                'bioreplicateId': rep_biorep[j],
                                'bioreplicateUniqueId': search_id(rep_biorep[j],rep_id_list) ,
                                'metabo_name' : k,
                                'cheb_id': cheb_id
                            }
                            metabo_rep_filtered = {k: v for k, v in metabo_rep.items() if v is not None}
                            if len(metabo_rep_filtered)>0:
                                db.addRecord('MetabolitePerExperiment', metabo_rep_filtered)
                    if list_abundances:
                        for h in list_abundances:
                            member_id = search_id(h,mem_name_id_list)
                            abundance ={
                                'studyId': study_id,
                                'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                                'experimentId': info['Experiment_ID'][i],
                                'bioreplicateId': rep_biorep[j],
                                'bioreplicateUniqueId' : search_id(rep_biorep[j],rep_id_list) ,
                                'strainId': search_id(member_id,mem_id_list),
                                'memberId': member_id
                            }
                            abundance_filtered = {k: v for k, v in abundance.items() if v is not None}
                            if len(abundance_filtered)>0:
                                db.addRecord('Abundances', abundance_filtered)
                    if list_counts:
                        for m in list_counts:
                            member_id = search_id(m,mem_name_id_list)
                            FC_counts = {
                                'studyId': study_id,
                                'experimentUniqueId': search_id(info['Experiment_ID'][i],biorep_id_list),
                                'experimentId': info['Experiment_ID'][i],
                                'bioreplicateId': rep_biorep[j],
                                'bioreplicateUniqueId' : search_id(rep_biorep[j],rep_id_list) ,
                                'strainId': search_id(member_id,mem_id_list),
                                'memberId': member_id
                            }
                            FC_counts_filtered = {k: v for k, v in FC_counts.items() if v is not None}
                            if len(FC_counts_filtered)>0:
                                db.addRecord('FC_Counts', FC_counts_filtered)

        if 'Biological_Replicate_id' in replicate_metadata:
            for i in range(num_rep_metadata):
                biorep_metadata = {
                    'studyId' : study_id,
                    'bioreplicateUniqueId': search_id(replicate_metadata['Biological_Replicate_id'][i],rep_id_list),
                    'bioreplicateId': replicate_metadata['Biological_Replicate_id'][i],
                    'biosampleLink': replicate_metadata['Biosample_link'][i],
                    'bioreplicateDescrition': replicate_metadata['Description'][i]
                }
                biorep_metadata_filtered = {k: v for k, v in biorep_metadata.items() if v is not None}
                if len(biorep_metadata_filtered)>0:
                    db.addRecord('BioReplicatesMetadata', biorep_metadata_filtered)

        return study_id, errors, errors_logic, study['studyUniqueID'],study['projectUniqueID'], project_id

    else:
        print("ERROR")
        return None, errors, [], None, None, None

#function that stripst columns where more than one value is allowed
def stripping_method(cell):
    if ',' in cell:
        samples = [sample.strip() for sample in cell.split(',')]
        return samples
    else:
        return [cell.strip()]

# function that search the id given a value
def search_id(search_value, data_list):
    # Using a for loop to iterate over the list of tuples
    for key, value in data_list:
        if key == search_value:
            return value  # Return the value if the key is found
    return None
