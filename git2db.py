__author__ = 'atlanmod'

import mysql.connector
from mysql.connector import errorcode
import re
from datetime import datetime
from git import *
from gitquerier_gitpython import GitQuerier
import config_db


class Git2Db():

    def __init__(self, db_name, git_repo_path, before_date, line_details, logger):
        self.logger = logger
        self.git_repo_path = git_repo_path
        self.db_name = db_name
        self.before_date = before_date
        self.get_line_details = line_details
        self.querier = GitQuerier(git_repo_path, logger)

        self.cnx = mysql.connector.connect(**config_db.CONFIG)
        self.set_database()

    def insert_repo(self):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO repository " \
                "VALUES (%s, %s)"
        arguments = [None, self.db_name]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM repository " \
                "WHERE name = %s"
        arguments = [self.db_name]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_reference(self, repo_id, ref_name, ref_type):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO reference " \
                "VALUES (%s, %s, %s, %s)"
        arguments = [None, repo_id, ref_name, ref_type]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def select_reference_name(self, repo_id, ref_id):
        cursor = self.cnx.cursor()
        query = "SELECT name " \
                "FROM reference " \
                "WHERE id = %s and repo_id = %s"
        arguments = [ref_id, repo_id]
        cursor.execute(query, arguments)
        name = cursor.fetchone()[0]
        cursor.close()
        return name

    def select_reference_id(self, repo_id, ref_name):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM reference " \
                "WHERE name = %s and repo_id = %s"
        arguments = [ref_name, repo_id]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_developer(self, name, email):
        cursor = self.cnx.cursor()

        if not name:
            name = '_unknown'
        if not email:
            email = '_unknown'

        query = "INSERT IGNORE INTO developer " \
                "VALUES (%s, %s, %s)"
        arguments = [None, name, email]
        cursor.execute(query, arguments)
        self.cnx.commit()

        query = "SELECT id " \
                "FROM developer " \
                "WHERE name = %s AND email = %s"
        arguments = [name, email]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def insert_commit(self, repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO commit " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [None, repo_id, sha, message.strip(), author_id, committer_id, authored_date, committed_date, size]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def insert_commit_parents(self, parents, commit_id, sha, repo_id):
        cursor = self.cnx.cursor()
        for parent in parents:
            try:
                parent_id = self.select_commit(parent.hexsha)
            except:
                parent_id = None
                self.logger.warning("Git2Db: parent commit id not found! SHA parent " + str(parent.hexsha))

            query = "INSERT IGNORE INTO commit_parent " \
                    "VALUES (%s, %s, %s, %s, %s)"

            if parent_id:
                arguments = [repo_id, commit_id, sha, parent_id, parent.hexsha]
            else:
                arguments = [repo_id, commit_id, sha, None, parent.hexsha]

            cursor.execute(query, arguments)
            self.cnx.commit()

        cursor.close()
        return

    def insert_commit_in_reference(self, repo_id, commit_id, ref_id):
        cursor = self.cnx.cursor()
        query = "INSERT INTO commit_in_reference " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, commit_id, ref_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def select_commit(self, sha):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM " + self.db_name + ".commit " \
                "WHERE sha = %s"
        arguments = [sha]
        cursor.execute(query, arguments)
        id = cursor.fetchone()[0]
        cursor.close()
        return id

    def select_file_id(self, repo_id, name, ref_id):
        cursor = self.cnx.cursor()
        query = "SELECT id " \
                "FROM file " \
                "WHERE name = %s AND repo_id = %s AND ref_id = %s"
        arguments = [name, repo_id, ref_id]
        cursor.execute(query, arguments)
        try:
            id = cursor.fetchone()[0]
        except:
            id = None
        cursor.close()
        return id

    def insert_file(self, repo_id, name, ext, ref_id):
        cursor = self.cnx.cursor()
        query = "INSERT IGNORE INTO file " \
                "VALUES (%s, %s, %s, %s, %s)"
        arguments = [None, repo_id, name, ext, ref_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def insert_file_renamed(self, repo_id, current_file_id, previous_file_id):
        cursor = self.cnx.cursor()

        query = "INSERT IGNORE INTO file_renamed " \
                "VALUES (%s, %s, %s)"
        arguments = [repo_id, current_file_id, previous_file_id]
        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def insert_file_modification(self, commit_id, file_id, status, additions, deletions, changes, patch_content):
        cursor = self.cnx.cursor()
        query = "INSERT INTO file_modification " \
                "VALUES (NULL, %s, %s, %s, %s, %s, %s, %s)"
        arguments = [commit_id, file_id, status, additions, deletions, changes, patch_content]
        cursor.execute(query, arguments)
        last_id = cursor.lastrowid
        self.cnx.commit()
        cursor.close()
        return last_id

    def insert_line_details(self, file_modification_id, detail):
        cursor = self.cnx.cursor()
        query = "INSERT INTO line_detail " \
                "VALUES (%s, %s, %s, %s, %s, %s, %s)"

        arguments = [file_modification_id, detail[0], detail[1], detail[2], detail[3], detail[4], detail[5]]

        cursor.execute(query, arguments)
        self.cnx.commit()
        cursor.close()
        return

    def get_ext(self, str):
        ext = str.split('.')[-1]
        return ext
        # try:
        #     searchObj = re.search(r"(\.([a-zA-Z])+)+$", str, re.M | re.I)
        #     ext = searchObj.group().strip(".")
        # except:
        #     self.logging.warning("Git2Db: file " + str + " has not extension")
        #     ext = None
        # return ext

    #not used, future extension
    def get_type(self, str):
        type = "text"
        if str.startswith('Binary files'):
            type = "binary"
        return type

    def get_info_contribution(self):
        repo_id = self.insert_repo()
        for reference in self.querier.get_references():
            ref_name = reference[0]
            ref_type = reference[1]

            print (ref_name + ',' + ref_type)

            if self.before_date:
                commits = self.querier.collect_all_commits_before_date(ref_name, self.before_date)
            else:
                commits = self.querier.collect_all_commits(ref_name)

            self.analyse_reference(ref_name, ref_type, repo_id)
            self.analyse_commits(commits, ref_name, repo_id)
            #fix parent table for missing parents
            self.fix_commit_parent_table(repo_id)
        return

    def analyse_reference(self, ref_name, ref_type, repo_id):
        self.insert_reference(repo_id, ref_name, ref_type)
        return

    def analyse_commit(self, commit, ref_id, repo_id):
        message = self.querier.get_commit_property(commit, "message")
        author_name = self.querier.get_commit_property(commit, "author.name")
        author_email = self.querier.get_commit_property(commit, "author.email")
        committer_name = self.querier.get_commit_property(commit, "committer.name")
        committer_email = self.querier.get_commit_property(commit, "committer.email")
        size = self.querier.get_commit_property(commit, "size")
        sha = self.querier.get_commit_property(commit, "hexsha")
        authored_date = datetime.fromtimestamp(self.querier.get_commit_property(commit, "authored_date")).strftime("%Y-%m-%d %H:%M:%S")
        committed_date = datetime.fromtimestamp(self.querier.get_commit_property(commit, "committed_date")).strftime("%Y-%m-%d %H:%M:%S")
        #insert author
        author_id = self.insert_developer(author_name, author_email)
        committer_id = self.insert_developer(committer_name, committer_email)
        #insert commit
        self.insert_commit(repo_id, sha, message, author_id, committer_id, authored_date, committed_date, size)

        commit_id = self.select_commit(sha)

        #insert parents of the commit
        self.insert_commit_parents(commit.parents, commit_id, sha, repo_id)
        #insert commits in reference
        self.insert_commit_in_reference(repo_id, commit_id, ref_id)

        try:
            if self.querier.commit_has_no_parents(commit):
                for diff in self.querier.get_diffs_no_parent_commit(commit):
                    file_path = diff[0]
                    ext = self.get_ext(file_path)

                    self.insert_file(repo_id, file_path, ext, ref_id)
                    file_id = self.select_file_id(repo_id, file_path, ref_id)

                    patch_content = re.sub(r'^(\w|\W)*\n@@', '@@', diff[1])
                    stats = self.querier.get_stats_for_file(commit, file_path)
                    status = self.querier.get_status(stats, diff)

                    #insert file modification
                    last_file_modification = self.insert_file_modification(commit_id, file_id, status,
                                                                      stats[0], stats[1], stats[2],
                                                                      patch_content)
                    if self.get_line_details:
                        line_details = self.querier.get_line_details(patch_content, ext)
                        for line_detail in line_details:
                            self.insert_line_details(last_file_modification, line_detail)
            else:
                for diff in self.querier.get_diffs(commit):
                    if self.querier.is_renamed(diff):
                        file_previous = self.querier.get_rename_from(diff)
                        ext_current = self.get_ext(file_previous)

                        file_current = self.querier.get_file_current(diff)

                        #insert new file
                        self.insert_file(repo_id, file_current, ext_current, ref_id)

                        #get id new file
                        current_file_id = self.select_file_id(repo_id, file_current, ref_id)

                        #retrieve the id of the previous file
                        previous_file_id = self.select_file_id(repo_id, file_previous, ref_id)

                        if not previous_file_id:
                            self.logger.warning("Git2Db: previous file id not found. commit message " + commit.message)

                        if current_file_id == previous_file_id:
                            self.logger.warning("Git2Db: previous file id is equal to current file id (" + str(current_file_id) + ") " + commit.message)

                        self.insert_file_renamed(repo_id, current_file_id, previous_file_id)
                        self.insert_file_modification(commit_id, current_file_id, "renamed", 0, 0, 0, None)
                    else:
                        #insert file
                        #if the file does not have a path, it won't be inserted
                        try:
                            file_path = self.querier.get_file_path(diff)

                            ext = self.get_ext(file_path)

                            stats = self.querier.get_stats_for_file(commit, file_path)
                            status = self.querier.get_status(stats, diff)

                            #if the file is new, add it
                            if self.querier.is_new_file(diff):
                                self.insert_file(repo_id, file_path, ext, ref_id)
                            file_id = self.select_file_id(repo_id, file_path, ref_id)

                            #insert file modification (additions, deletions)
                            patch_content = self.querier.get_patch_content(diff)
                            last_file_modification = self.insert_file_modification(commit_id, file_id, status,
                                                                              stats[0], stats[1], stats[2], patch_content)

                            if self.get_line_details:
                                line_details = self.querier.get_line_details(patch_content, ext)
                                for line_detail in line_details:
                                    self.insert_line_details(last_file_modification, line_detail)
                        except:
                            self.logger.warning("Git2Db: GitPython null file path " + str(sha) + " - " + str(message))
        except AttributeError as e:
            self.logger.error("Git2Db: GitPython just failed on commit " + str(sha) + " - " + str(message) + ". Details: " + str(e))
        finally:
            return

    def analyse_commits(self, commits, ref, repo_id):
        ref_id = self.select_reference_id(repo_id, ref)

        for c in commits:
            self.logger.info("Git2Db: analysing reference: " + ref + " -- commit " + str(commits.index(c)+1) + "/" + str(len(commits)) + " -- " + c.message)
            self.analyse_commit(c, ref_id, repo_id)
        return

    def fix_commit_parent_table(self, repo_id):
        cursor = self.cnx.cursor()
        query_select = "SELECT parent_sha " \
                       "FROM commit_parent " \
                       "WHERE parent_id IS NULL AND repo_id = %s"
        arguments = [repo_id]
        cursor.execute(query_select, arguments)
        row = cursor.fetchone()
        while row:
            parent_sha = row[0]
            parent_id = self.select_commit(parent_sha)
            query_update = "UPDATE commit_parent " \
                           "SET parent_id = %s " \
                           "WHERE parent_id IS NULL AND parent_sha = %s AND repo_id = %s "
            arguments = [parent_id, parent_sha, repo_id]
            cursor.execute(query_update, arguments)
            self.cnx.commit()
            row = cursor.fetchone()
        cursor.close()
        return

    def set_database(self):
        cursor = self.cnx.cursor()
        use_database = "USE " + self.db_name
        cursor.execute(use_database)
        cursor.close()

    def extract(self):
        start_time = datetime.now()
        self.get_info_contribution()
        self.querier.add_no_treated_extensions_to_log()
        end_time = datetime.now()
        self.cnx.close()

        minutes_and_seconds = divmod((end_time-start_time).total_seconds(), 60)
        self.logger.info("Git2Db: process finished after " + str(minutes_and_seconds[0])
                     + " minutes and " + str(round(minutes_and_seconds[1], 1)) + " secs")
        return