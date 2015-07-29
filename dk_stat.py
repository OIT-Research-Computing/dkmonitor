"""
This file contains the DkStat object that scans a given disk or directory
and stores the data in user and directory objects
"""

import os
import shutil
import time
from pwd import getpwuid
import operator
import datetime

import user_obj
import dir_obj
#import db_interface
from named_tuples import FileTuple


class DkStat:
    """
    This class is meant to gather stats on a disk or directory
    It stores stats in a directory object and separate user objects
    for each user
    """

    def __init__(self, system, search_dir):

        #Input search directory path verification exception
        try:
            os.listdir(search_dir)
        except:
            raise Exception("Directory path: {dir} is invalid.".format(dir=search_dir))

        self.search_time = 0
        self.user_hash = {}
        self.directory_obj = None
        self.system = system
        self.search_directory = search_dir
        #self.load_users_file("../user_txt_file2.txt")
        #print("Loaded")


    def dir_search(self, recursive_dir=None): #possibly divide into multiple fucntions
        """
        Searches through entire directory tree recursively
        Saves file info in a dict sorted by user
        """

        if recursive_dir == None:
            self.search_time = datetime.datetime.now()
            self.directory_obj = dir_obj.Directory(search_dir=self.search_directory,
                                                   system=self.system,
                                                   datetime=self.search_time) #Creates dir_obj

            self.dir_search(recursive_dir=self.search_directory) #starts recursive call

        else:
            if os.path.isdir(recursive_dir):
                content_list = os.listdir(recursive_dir)
                for i in content_list:
                    current_path = recursive_dir + '/' + i
                    if os.path.isfile(current_path): #If dir is a file, check when it was modified

                        #TODO consolidate all of these lines into a add_file function call
                        #divide CPU time into days
                        last_access = (time.time() - os.path.getatime(current_path)) / 86400
                        #Gets file size
                        file_size = int(os.path.getsize(current_path))
                        #gets user name
                        name = getpwuid(os.stat(current_path).st_uid).pw_name

                        file_tup = FileTuple(current_path, file_size, last_access)
                        self.directory_obj.add_file(file_tup) #Add file to directory obj

                        #if name has not already be found then add to user_hash
                        if name not in self.user_hash.keys():
                            self.user_hash[name] = user_obj.User(name,
                                                                 search_dir=self.search_directory,
                                                                 system=self.system,
                                                                 datetime=self.search_time)
                        self.user_hash[name].add_file(file_tup)

                    else:
                        try:
                            #recursive call on every directory
                            self.dir_search(recursive_dir=(current_path))
                        except OSError:
                            pass


    def export_data(self, db_obj):
        """Exports the file data from the User dict to a database object"""

        self.directory_obj.export_data(db_obj)
        for user in self.user_hash.keys():
            self.user_hash[user].export_data(db_obj)

    def email_users(self,
                    emailer_obj,
                    postfix,
                    last_access_threshold,
                    days_between_runs,
                    move_dir,
                    problem_threshold):
        """Flaggs users, and then sends out email warnings"""

        problem_lists = self.get_problem_users(problem_threshold)
        for user in self.user_hash.keys():
            self.user_hash[user].email_user(emailer_obj,
                                            postfix,
                                            last_access_threshold,
                                            days_between_runs,
                                            move_dir,
                                            problem_lists)


    def get_disk_use_percent(self):
        """Returns the disk use percentage of searched_directory"""

        use = shutil.disk_usage(self.search_directory)
        use_percentage = use.used / use.total
        return use_percentage * 100


    def get_problem_users(self, problem_threshold):
        """
        Returns a list of lists
        List in item one is the largest users of space
        List two is the largest holders of old data
        """

        stat_list = []
        problem_threshold = problem_threshold / 100
        flag_user_number = int(len(self.user_hash.keys()) * problem_threshold)
        for user in self.user_hash.keys():
            stats = self.user_hash[user].get_stats()
            bpad = stats[0]/stats[1] #Bytes per access day
            stat_list.append([user, stats[0], bpad])

        print("Total users: {flag}".format(flag=len(self.user_hash.keys())))
        print("Total Flagged users: {flag}".format(flag=flag_user_number))
        large_list = sorted(stat_list, key=operator.itemgetter(1), reverse=True)[:flag_user_number]
        print(large_list)
        old_list = sorted(stat_list, key=operator.itemgetter(2), reverse=True)[:flag_user_number]

        large_names = []
        old_names = []
        for i in range(flag_user_number):
            large_names.append(large_list[i][0])
            old_names.append(old_list[i][0])

        return [large_names, old_names] #TODO change to a named tuple


if __name__ == "__main__":
    pass



