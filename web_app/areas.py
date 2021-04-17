from datetime import datetime

from web_app import db
from web_app.models import User

X_POS = 0
Y_POS = 1


class Areas:
    point1 = set()
    point2 = set()

    Areas_dict = {
        (1.32, 2.43): set(),
        (31.7808, 35.2287): set(),
        (31.910665, 34.896717): set()
    }

    def getUsersInRadius(self, user, radius):
        userLocationX = user.current_area_x
        userLocationY = user.current_area_y
        areaX = user.current_area_x
        areaY = user.current_area_y
        profilesInArea = self.Areas_dict[(areaX, areaY)]
        result = set()
        for profile in profilesInArea:
            dist = self.distance((areaX, areaY), userLocationX, userLocationY)
            if dist <= radius and profile.email is not user.email:
                result.add(profile)
        return result

    def init_areas(self):
        all_users = User.query.all()
        for user in all_users:
            self.update(user, True)
        #print(self.Areas_dict)

    def update(self, user, to_initialized=False):
        min_dist = 9999999
        curr_x_min = 9999999
        curr_y_min = 9999999

        #  delete user from old position in area dict
        if not to_initialized and (
                user.current_area_x, user.current_area_y) in self.Areas_dict.keys():
            try:
                self.Areas_dict[(user.current_area_x, user.current_area_y)].remove(user)
            except:
                pass

        for key in self.Areas_dict:
            curr_dist = self.distance(key, user.pos_x, user.pos_y)
            if curr_dist < min_dist:
                min_dist = curr_dist
                curr_x_min = key[X_POS]
                curr_y_min = key[Y_POS]

        # add user to relevant place in area dict
        self.Areas_dict[(curr_x_min, curr_y_min)].add(user)
        return curr_x_min, curr_y_min

    def distance(self, key, user_pos_x, user_pos_y):
        return (key[X_POS] - user_pos_x) ** 2 + (key[Y_POS] - user_pos_y) ** 2


area = Areas()
