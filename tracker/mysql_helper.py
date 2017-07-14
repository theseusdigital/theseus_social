import MySQLdb

def safe_insert(tablename, insertdict):
	columns = insertdict.keys()
	values_str = ",".join(["%s"]*len(columns))
	columns_str = ",".join(columns)
	query_data = [insertdict[c] for c in columns]
	query = "insert into %s(%s) values(%s)"%(tablename,columns_str,values_str)
	# print query
	return (query,query_data)

def safe_update(tablename, uniquecolumns, updatedict):
	query_data = []
	where_data = []
	set_clauses = []
	where_clauses = []
	for col,value in updatedict.iteritems():
		if col in uniquecolumns:
			where_clauses.append("{0} = %s".format(col))
			where_data.append(value)
			continue
		query_data.append(value)
		setclause = "{0} = %s".format(col)
		set_clauses.append(setclause)
	query_data.extend(where_data)
	set_str = ",".join(set_clauses)
	where_str = " and ".join(where_clauses)
	query = "update %s set %s where %s"%(tablename,set_str,where_str)
	# print query
	return (query,query_data)