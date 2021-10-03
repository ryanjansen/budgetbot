import psycopg2


class Database:
    def __init__(self, dbname, user):
        self.dbname = dbname
        self.user = user

    def __execute(self, command, values, has_data=False):
        data = None
        try:
            conn = psycopg2.connect(dbname=self.dbname, user=self.user)
            cur = conn.cursor()
            cur.execute(command, values)
            if has_data:
                data = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
            if data:
                return data

    def add_user(self, user_name, chat_id):
        command = """ INSERT INTO users(user_name, chat_id) VALUES(%s, %s) RETURNING user_id;"""
        values = (user_name, chat_id)
        return self.__execute(command, values, True)

    def get_user(self, chat_id):
        command = """SELECT user_id FROM users WHERE chat_id = %s"""
        values = (chat_id, )
        user =  self.__execute(command, values, True)
        if user:
            return user
        else:
            return False

    def add_expense(self, user_id, amount, date, category):
        command = """ INSERT INTO expenses(user_id, amount, date, category) VALUES(%s, %s, %s, %s);"""
        values = (user_id, amount, date, category)
        self.__execute(command, values)

    def get_expenses(self, user_id, date):
        command = """SELECT amount, date, category FROM expenses WHERE user_id = %s 
                     AND EXTRACT(YEAR FROM date) = %s AND EXTRACT(MONTH FROM date) = %s"""
        values = (user_id, date.year, date.month)
        return self.__execute(command, values, True)

    def delete_last_expense(self, user_id):
        command = """DELETE FROM expenses WHERE expense_id in (SELECT expense_id FROM expenses WHERE user_id = %s 
                     ORDER BY date DESC, expense_id DESC LIMIT 1) 
                     RETURNING amount, date, category; """
        values = (user_id,)
        return self.__execute(command, values, True)
