from utils.database_connector import read_query, write_query

#________________________________________SELECT Queries________________________________________#

def select_all_countries():
	select_countries_query_string = f"""
	SELECT * FROM country;
	"""
	df = read_query(select_countries_query_string)
	return df

def select_all_platforms():
	platform_query_string = f"""
	SELECT * FROM platform
	"""
	df = read_query(platform_query_string)
	return df

def select_all_entities():
	select_entities_query_string = f"""
	SELECT * FROM entity;
	"""
	df = read_query(select_entities_query_string)
	return df

def select_all_users(application_decision = None):
	select_users_query_string = f"""
	SELECT * FROM vetted_user 
	"""
	if application_decision is not None:
		select_users_query_string += f"""
		WHERE application_decision = '{application_decision}';
		"""
	df = read_query(select_users_query_string)
	return df

def verify_user(email_in):
	"""Define a template so that the function always returns the expected fields, empty or not"""
	user_info = {"full_name":"", "hashed_password":"", "is_admin":False, "application_decision":""}

	user_query_string = f"""
	SELECT
		CONCAT(first_name, ' ', last_name) AS full_name,
		is_admin,
		hashed_password,
		application_decision
	FROM vetted_user
	WHERE work_email = '{email_in}';
	"""
	df = read_query(user_query_string)
	try:
		user_info["full_name"] = df.iloc[0]["full_name"]
		user_info["hashed_password"] = df.iloc[0]["hashed_password"]
		user_info["is_admin"] = df.iloc[0]["is_admin"]
		user_info["application_decision"] = df.iloc[0]["application_decision"]
	except Exception as e:
		pass
	return user_info

def select_all_reports(url_in = None):
	reports_query_string = f"""
	SELECT
		rp.open_report_timestamp,
		CONCAT(vu.first_name, " ", vu.last_name) AS reporing_user,
		vu.affiliation_name AS reporting_entity,
		rp.platform_name AS platform,
		rp.url,
		rp.report_type,
		rp.screenshot_url,
		rp.close_report_timestamp,
		rp.platform_decision,
		rp.policy,
		rp.appeal
	FROM
		report AS rp
		INNER JOIN
		vetted_user AS vu
		ON vu.work_email = rp.reporting_user
	"""
	if url_in is not None:
		reports_query_string += f"""
		WHERE url = '{url_in}'
		"""
	reports_query_string += f"""
	ORDER BY rp.open_report_timestamp DESC;
	"""
	df = read_query(reports_query_string)
	return df

def select_user_reports(email_in, url_in = None):
	reports_query_string = f"""
	SELECT
		open_report_timestamp,
		platform_name AS platform,
		url,
		report_type,
		screenshot_url,
		close_report_timestamp,
		platform_decision,
		policy,
		appeal
	FROM report
	WHERE reporting_user = '{email_in}'
	"""
	if url_in is not None:
		reports_query_string += f"""
		WHERE url = '{url_in}'
		"""
	#Add a nonmandatory sorting:
	reports_query_string += f"""
	ORDER BY open_report_timestamp DESC;
	"""
	df = read_query(reports_query_string)
	return df

def select_reports_types():
	types_query_string = f"""
	SELECT * FROM report_classification;
	"""
	df = read_query(types_query_string)
	return df

def select_pending_password_resets():
	password_resets_query_string = f"""
	WITH reset_counts_cte AS(
	SELECT
		work_email,
		COUNT(id_request) AS resets_count
	FROM password_reset_request WHERE admin_decision = 'Approved'
	GROUP BY work_email
	),
	analytics_cte AS(
	SELECT
		pr.id_request,
		pr.work_email,
		vt.first_name,
    	vt.last_name,
    	vt.affiliation_name,
    	pr.request_date,
    	pr.reset_reason,
    	DATEDIFF(
			pr.request_date,
			LAG(pr.request_date) OVER (PARTITION BY pr.work_email ORDER BY pr.request_date)
			) AS days_since_last_request,
    	COALESCE(rc.resets_count, 0) AS resets_count,
        reset_completed
	FROM
		vetted_user AS vt
		INNER JOIN
		password_reset_request AS pr
		ON pr.work_email = vt.work_email
		LEFT JOIN reset_counts_cte AS rc
		ON rc.work_email = vt.work_email
	)
	SELECT * FROM analytics_cte WHERE reset_completed = 0;
	"""
	df = read_query(password_resets_query_string)
	return df

def check_pending_reset(email_in):
	pending_reset_query_string = f"""
	SELECT 'Yes' AS has_pending_request FROM password_reset_request
	WHERE work_email = '{email_in}' AND reset_completed = 0
	"""
	df = read_query(pending_reset_query_string)
	try:
		has_pending_request = df.iloc[0]["has_pending_request"]
	except Exception as e:
		return ""
	return has_pending_request

def select_new_password(id_request_in):
	new_password_query_string = f"""
	SELECT new_password FROM password_reset_request WHERE id_request = {id_request_in};
	"""
	try:
		df = read_query(new_password_query_string)
		new_password = df.iloc[0]["new_password"]
	except Exception as e:
		return "Failed"
	return new_password

#________________________________________INSERT Queries________________________________________#

def add_entity(affiliation_in, website_in, signatory_status_in, country_in):
	df = select_all_entities()
	if affiliation_in in df["entity_name"].values:
		return "Existing entity"

	add_entity_query_string = f"""
	INSERT INTO entity (
		entity_name,
		website,
		signatory_of_code_of_practice_on_disinformation,
		country_name
	)
	VALUES ('{affiliation_in}', '{website_in}', '{signatory_status_in}', '{country_in}');
	"""
	result = write_query(add_entity_query_string)
	return result


def add_user(email_in, hashed_password_in, first_name_in, last_name_in, affiliation_in, date_in):
	df = select_all_users()
	if email_in in df["work_email"].values:
		return "Existing User"

	add_user_query_string = f"""
	INSERT INTO vetted_user(
		work_email,
		hashed_password,
		first_name,
		last_name,
		affiliation_name,
		application_date
	)
	VALUES ('{email_in}', '{hashed_password_in}', '{first_name_in}', '{last_name_in}', '{affiliation_in}', '{date_in}');
	"""

	result = write_query(add_user_query_string)
	return result

def add_report(current_date_in, email_in, platform_in, url_in, type_in, screenshot_url_in,
	answer_date_in, decision_in, policy_in, appeal_in):
	df = select_all_reports(url_in)
	if not df.empty:
		return "A report with the specified url already exists. Submission denied."
	
	add_report_query_string = f"""
	INSERT INTO report(
		open_report_timestamp,
		reporting_user,
		platform_name,
		url,
		report_type,
		screenshot_url,
		close_report_timestamp,
		platform_decision,
		policy,
		appeal
	)
	SELECT
		'{current_date_in}',
		'{email_in}',
		'{platform_in}',
		'{url_in}',
		'{type_in}',
		CASE WHEN '{screenshot_url_in}' = 'None' THEN NULL ELSE '{screenshot_url_in}' END,
		CASE WHEN '{answer_date_in}' = 'None' THEN NULL ELSE '{answer_date_in}' END,
		CASE WHEN '{decision_in}' = 'None' THEN NULL ELSE '{decision_in}' END,
		CASE WHEN '{policy_in}' = 'None' THEN NULL ELSE '{policy_in}' END,
		CASE WHEN '{appeal_in}' = 'None' THEN NULL ELSE '{appeal_in}' END;
	"""
	result = write_query(add_report_query_string)
	return result

def add_password_reset_request(user_status, date_in, email_in, reason_in, old_password_in, new_password_in):
	add_request_query_string = f"""
	INSERT INTO password_reset_request(request_date, work_email, reset_reason, old_password, new_password)
	VALUES ('{date_in}', '{email_in}', '{reason_in}', '{old_password_in}', '{new_password_in}')
	"""

	has_pending_request = check_pending_reset(email_in)

	if user_status == "Approved" and not has_pending_request == "Yes":
		result = write_query(add_request_query_string)
	elif user_status == "Approved":
		result = "There already is a pending password request for this user."
	elif user_status == "Pending":
		result = "You cannot reset your password while your application is pending."
	else:
		result = "This user is either banned or unknown."
	return result
#________________________________________UPDATE Queries________________________________________#

def update_report(platform_in, url_in, type_in, screenshot_in,
	answer_date_in, decision_in, policy_in, appeal_in):
	update_report_query_string = f"""
	UPDATE report
	SET
		platform_name = '{platform_in}',
		url = CASE WHEN '{url_in}' = '' THEN url ELSE '{url_in}' END,
		report_type = NULLIF('{type_in}', ''),
		screenshot_url = NULLIF('{screenshot_in}', ''),
		close_report_timestamp = NULLIF('{answer_date_in}', ''),
		platform_decision = NULLIF('{decision_in}', ''),
		policy = NULLIF('{policy_in}', ''),
		appeal = NULLIF('{appeal_in}', '')
	WHERE url = '{url_in}';
	"""
	result = write_query(update_report_query_string)
	return result

def update_application_decision(admin_email_in, admin_decision_in, decision_date_in, users_tuple_in):
	update_applications_query_string = f"""
	UPDATE vetted_user
	SET
		application_decision = '{admin_decision_in}',
		decision_date = '{decision_date_in}',
		decision_author = '{admin_email_in}'
	"""
	if len(users_tuple_in) > 1:
		update_applications_query_string += f"""
		WHERE work_email IN {users_tuple_in};
		"""
	else:
		update_applications_query_string += f"""
		WHERE work_email = '{users_tuple_in[0]}';
		""" #To deal with trailing comma when length of tuple is 1
	result = write_query(update_applications_query_string)
	return result

def update_password_reset_decision(decision_in, decision_date_in, id_request_in):
	update_requests_query_string = f"""
	UPDATE password_reset_request
	SET
		admin_decision = '{decision_in}',
		admin_decision_date = '{decision_date_in}',
		reset_completed = 1
	WHERE id_request = {id_request_in};
	"""
	result = write_query(update_requests_query_string)
	return result

def update_password(user_email_in, new_password_in):
	update_password_query_string = f"""
	UPDATE vetted_user
	SET
		hashed_password = '{new_password_in}'
	WHERE work_email = '{user_email_in}';
	"""
	result = write_query(update_password_query_string)
	return result

def update_admin(decision_in, email_in):
	update_admin_query_string = f"""
	UPDATE vetted_user
	SET is_admin = {decision_in}
	WHERE work_email = '{email_in}'
	"""
	result = write_query(update_admin_query_string)
	return result

#________________________________________DELETE Queries________________________________________#
def delete_report(url_in):
	delete_report_query = f"""
	DELETE FROM report
	WHERE url = '{url_in}'
	"""
	result = write_query(delete_report_query)
	return result

#______________________Custom Functions execute multiple queries in a chain______________________#

def register_user(email_in, hashed_password_in, first_name_in, last_name_in, affiliation_in, 
	date_in, website_in, signatory_status_in, country_in):
	add_entity(affiliation_in, website_in, signatory_status_in, country_in)
	return add_user(email_in, hashed_password_in, first_name_in.title(), last_name_in.title(), affiliation_in, date_in)

def decide_password_reset(decision_in, decision_date_in, id_request_in, user_email_in):
	new_password_in = select_new_password(id_request_in)
	if decision_in == "Approved" and new_password_in != "Failed":
		update_password_reset_decision(decision_in, decision_date_in, id_request_in)
		update_password(user_email_in, new_password_in)
	elif decision_in == "Rejected":
		update_password_reset_decision(decision_in, decision_date_in, id_request_in)
	