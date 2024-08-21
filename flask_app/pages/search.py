"""
Search for studies based on name, used metabolites, microbial strains, and
other criteria.
"""

from flask import render_template
import sqlalchemy as sql
import pandas as pd

from flask_app.db import get_connection
from flask_app.forms.search_form import SearchForm

from src.db_functions import dynamical_query

# TODO (2024-08-20) Put structured data into data frame, render properly
# -> Link to metabolite/member
# -> Metabolite page (pages/metabolite.py)
# -> Strain page (pages/strain.py)
#
# TODO (2024-08-20) Use SQLalchemy model instead


def search_index_page():
    form = SearchForm()

    if form.validate_on_submit():
        query = dynamical_query([{ 'option': form.option.data, 'value': form.value.data }])

        with get_connection() as conn:
            studyIds = [studyId for (studyId,) in conn.execute(sql.text(query))]

            if len(studyIds) == 0:
                message = "Couldn't find a study with these parameters."
                return render_template("pages/search/index.html", form=form, error=message)

            results = [get_general_info(studyId, conn) for studyId in studyIds]

            return render_template(
                "pages/search/index.html",
                form=form,
                results=results,
            )

    return render_template("pages/search/index.html", form=form)



def get_general_info(studyId, conn):
    params = { 'studyId': studyId }

    query = f"""
        SELECT studyId, studyName, studyDescription, studyURL
        FROM Study
        WHERE studyId = :studyId
    """
    result = conn.execute(sql.text(query), params).one()._asdict()

    query = f"""
        SELECT memberName, NCBId
        FROM Strains
        WHERE studyId = :studyId
        ORDER BY memberName ASC
    """
    micro_strains = conn.execute(sql.text(query), params).all()
    result['members'] = [(name, id) for (name, id) in micro_strains]

    query = f"""
        SELECT DISTINCT technique
        FROM TechniquesPerExperiment
        WHERE studyId = :studyId
        ORDER BY technique ASC
    """
    techniques = conn.execute(sql.text(query), params).scalars()
    result['techniques'] = [name for name in techniques]

    query = f"""
        SELECT DISTINCT metabo_name, cheb_id
        FROM MetabolitePerExperiment
        WHERE studyId = :studyId
        ORDER BY metabo_name ASC
    """
    metabolites = conn.execute(sql.text(query), params).all()
    result['metabolites'] = [(name, cheb_id) for (name, cheb_id) in metabolites]

    return result
