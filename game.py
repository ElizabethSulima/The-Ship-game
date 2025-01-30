import random
from abc import ABC, abstractmethod
from typing import Literal

from PyQt5.QtGui import QVector2D  # pylint:disable=E0611

from constants import Sprite as sp
from core import GameAPI, Image, Marker

red_team: list = []
green_team: list = []
barriers: list = []


class AbstractWarShip(ABC):
    @abstractmethod
    def attack(self):
        pass

    @abstractmethod
    def move(self, x: int, y: int):
        pass


class WarShip(AbstractWarShip):
    def __init__(
        self,
        marker: Marker,
        position_x: int,
        position_y: int,
        color_team: Literal["red", "green"],
    ):
        self.marker = marker
        self.position_x = position_x
        self.position_y = position_y
        self.color_team = color_team

    def move(self, x, y):
        self.marker.moveTo(x, y)
        self.position_x = x
        self.position_y = y


class Destroyer(WarShip):
    def __init__(
        self,
        marker: Marker,
        color_team: Literal["red", "green"],
        name: str,
        position_x: int,
        position_y: int,
    ):
        super().__init__(marker, position_x, position_y, color_team)
        self.name = name
        self.damage = 30
        self.health_full = 15
        self.health_current = self.health_full
        self.speed = 4

    def attack(self):
        attac_coordinates = [
            (self.position_x - 1, self.position_y - 1),
            (self.position_x - 1, self.position_y),
            (self.position_x, self.position_y - 1),
            (self.position_x, self.position_y + 1),
            (self.position_x + 1, self.position_y),
            (self.position_x + 1, self.position_y - 1),
            (self.position_x - 1, self.position_y + 1),
            (self.position_x + 1, self.position_y + 1),
        ]
        if self.color_team == "green":
            log_attack = self.deal_damage(red_team, attac_coordinates)
            return log_attack

        if self.color_team == "red":
            log_attack = self.deal_damage(green_team, attac_coordinates)
            return log_attack

    def deal_damage(self, team_list, attac_coordinates):
        targets_list = []
        log_list = []
        for cage in attac_coordinates:
            for ship in team_list:
                if cage == (ship.position_x, ship.position_y):
                    targets_list.append(ship)

        if len(targets_list) > 0:
            damage_count = self.damage / len(targets_list)
            for ship in targets_list:
                difference_damage = ship.taking_damage(damage_count, 1)
                log_list.append((ship.name, int(difference_damage), self.name))

        return log_list

    def taking_damage(self, damage_count, distance=0):
        if distance >= 2:
            damage_count = damage_count / 2
            self.health_current -= damage_count
            self.marker.setHealth(self.health_current / self.health_full)
        else:
            self.health_current -= damage_count
            self.marker.setHealth(self.health_current / self.health_full)

        return abs(self.health_current - damage_count)

    def move(self, x, y):
        vector = QVector2D(self.position_x, self.position_y)
        distance = int(vector.distanceToPoint(QVector2D(x, y)))
        if distance <= self.speed:
            super().move(x, y)


class Cruiser(WarShip):
    def __init__(
        self,
        marker: Marker,
        color_team: Literal["red", "green"],
        name: str,
        position_x: int,
        position_y: int,
    ):
        super().__init__(marker, position_x, position_y, color_team)
        self.name = name
        self.damage = 15
        self.health_full = 30
        self.health_current = self.health_full
        self.speed = 3

    def attack(self):
        attack_coordinates = []
        for i in range(7):
            coordinates_x = (self.position_x, i)
            coordinates_y = (i, self.position_y)
            if (self.position_x, self.position_y) != coordinates_x:
                attack_coordinates.append(coordinates_x)
            if (self.position_x, self.position_y) != coordinates_y:
                attack_coordinates.append(coordinates_y)

        cruiser_x = []
        cruiser_y = []
        cliffs_x = []
        cliffs_y = []

        for barrier in barriers:
            if (
                barrier.position_x,
                barrier.position_y,
            ) in attack_coordinates and isinstance(barrier, Cliff):
                if barrier.position_x == self.position_x:
                    cliffs_x.append(barrier)
                elif barrier.position_y == self.position_y:
                    cliffs_y.append(barrier)

        if self.color_team == "green":
            self.get_enemies(
                red_team,
                cruiser_x,
                cruiser_y,
                attack_coordinates,
            )

        if self.color_team == "red":
            self.get_enemies(
                green_team,
                cruiser_x,
                cruiser_y,
                attack_coordinates,
            )

        if self.color_team == "red":
            log_attack_x = self.deal_damage(cruiser_y, cliffs_y, "position_x")
            log_attack_y = self.deal_damage(cruiser_x, cliffs_x, "position_y")
            return log_attack_x + log_attack_y

        if self.color_team == "green":
            log_attack_x = self.deal_damage(cruiser_y, cliffs_y, "position_x")
            log_attack_y = self.deal_damage(cruiser_x, cliffs_x, "position_y")
            return log_attack_x + log_attack_y

    def deal_damage(self, cruiser_axis, cliffs, axis):
        targets_list = []
        log_list = []
        for ship in cruiser_axis:
            distance_to_ship = abs(getattr(ship, axis) - getattr(self, axis))
            if len(cliffs) > 0:
                for cliff in cliffs:
                    distance_to_cliff = abs(
                        getattr(cliff, axis) - getattr(self, axis)
                    )
                    if distance_to_cliff > distance_to_ship:
                        targets_list.append((ship, distance_to_ship))
            else:
                targets_list.append((ship, distance_to_ship))

        if len(targets_list) > 0:
            damage_count = self.damage / len(targets_list)
            for ship, distance in targets_list:
                difference_damage = ship.taking_damage(damage_count, distance)
                log_list.append((ship.name, int(difference_damage), self.name))

        return log_list

    def taking_damage(self, damage_count, distance=0):
        if distance >= 2:
            damage_count = damage_count / 2
            self.health_current -= damage_count
            self.marker.setHealth(self.health_current / self.health_full)
        else:
            self.health_current -= damage_count
            self.marker.setHealth(self.health_current / self.health_full)

        return abs(self.health_current - damage_count)

    def get_enemies(self, team_list, list_x, list_y, coordinates):
        for warship in team_list:
            if (warship.position_x, warship.position_y) in coordinates:
                if warship.position_x == self.position_x:
                    list_x.append(warship)
                elif warship.position_y == self.position_y:
                    list_y.append(warship)

    def move(self, x, y):
        vector = QVector2D(self.position_x, self.position_y)
        distance = int(vector.distanceToPoint(QVector2D(x, y)))
        if distance <= self.speed:
            super().move(x, y)


class Battleship(WarShip):
    def __init__(
        self,
        marker: Marker,
        color_team: Literal["red", "green"],
        name: str,
        position_x: int,
        position_y: int,
    ):
        super().__init__(marker, position_x, position_y, color_team)
        self.name = name
        self.damage = 20
        self.health_full = 50
        self.health_current = self.health_full
        self.speed = 2

    def attack(self):
        attack_coordinates = []
        for i in range(7):
            coordinates_x = (self.position_x, i)
            coordinates_y = (i, self.position_y)
            if (self.position_x, self.position_y) != coordinates_x:
                attack_coordinates.append(coordinates_x)
            if (self.position_x, self.position_y) != coordinates_y:
                attack_coordinates.append(coordinates_y)

        battleship_x = []
        battleship_y = []
        cliffs_x = []
        cliffs_y = []

        for barrier in barriers:
            if (
                barrier.position_x,
                barrier.position_y,
            ) in attack_coordinates and isinstance(barrier, Cliff):
                if barrier.position_x == self.position_x:
                    cliffs_x.append(barrier)
                elif barrier.position_y == self.position_y:
                    cliffs_y.append(barrier)

        if self.color_team == "green":
            self.get_enemies(
                red_team,
                battleship_x,
                battleship_y,
                attack_coordinates,
            )

        if self.color_team == "red":
            self.get_enemies(
                green_team,
                battleship_x,
                battleship_y,
                attack_coordinates,
            )

        if self.color_team == "red":
            log_attack_x = self.deal_damage(
                battleship_y, cliffs_y, "position_x"
            )
            log_attack_y = self.deal_damage(
                battleship_x, cliffs_x, "position_y"
            )

            return log_attack_x + log_attack_y

        if self.color_team == "green":
            log_attack_x = self.deal_damage(
                battleship_y, cliffs_y, "position_x"
            )
            log_attack_y = self.deal_damage(
                battleship_x, cliffs_x, "position_y"
            )

            return log_attack_x + log_attack_y

    def deal_damage(self, battleship_axis, cliffs, axis):
        targets_list = []
        log_list = []
        for ship in battleship_axis:
            if len(cliffs) > 0:
                distance_to_ship = abs(
                    getattr(ship, axis) - getattr(self, axis)
                )
                for cliff in cliffs:
                    distance_to_cliff = abs(
                        getattr(cliff, axis) - getattr(self, axis)
                    )
                    if distance_to_cliff > distance_to_ship:
                        targets_list.append(ship)
            else:
                targets_list.append(ship)

        if len(targets_list) > 0:
            damage_count = self.damage / len(targets_list)
            for ship in targets_list:
                difference_damage = ship.taking_damage(damage_count)
                log_list.append((ship.name, int(difference_damage), self.name))

        return log_list

    def taking_damage(self, damage_count, distance=None):
        if damage_count > 10:
            self.health_current -= damage_count
            self.marker.setHealth(self.health_current / self.health_full)

        return abs(self.health_current - damage_count)

    def get_enemies(self, team_list, list_x, list_y, coordinates):
        for warship in team_list:
            if (warship.position_x, warship.position_y) in coordinates:
                if warship.position_x == self.position_x:
                    list_x.append(warship)
                elif warship.position_y == self.position_y:
                    list_y.append(warship)

    def move(self, x, y):
        vector = QVector2D(self.position_x, self.position_y)
        distance = int(vector.distanceToPoint(QVector2D(x, y)))
        if distance <= self.speed:
            super().move(x, y)


class Island:
    def __init__(self, image: Image, position_x: int, position_y: int):
        self.image = image
        self.position_x = position_x
        self.position_y = position_y


class Cliff:
    def __init__(self, image: Image, position_x: int, position_y: int):
        self.image = image
        self.position_x = position_x
        self.position_y = position_y


class Game(object):
    current_team: Literal["green", "red"] = "red"
    warship: WarShip | None = None
    letters = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G"}

    def start(self, api: GameAPI) -> None:
        api.addMessage("start")
        api.addMessage(f"-- {self.current_team} --")
        red_team.append(
            Destroyer(
                api.addMarker(sp.RED_DESTROYER, x=6, y=1), "red", "G-101", 6, 1
            )
        )
        red_team.append(
            Cruiser(  # type:ignore[arg-type]
                api.addMarker(sp.RED_CRUISER, x=6, y=3), "red", "Kolberg", 6, 3
            )
        )
        red_team.append(
            Battleship(  # type:ignore[arg-type]
                api.addMarker(sp.RED_BATTLESHIP, x=6, y=5),
                "red",
                "Koening",
                6,
                5,
            )
        )
        green_team.append(
            Destroyer(
                api.addMarker(sp.GREEN_DESTROYER, x=0, y=1),
                "green",
                "Medea",
                0,
                1,
            )
        )
        green_team.append(
            Cruiser(  # type:ignore[arg-type]
                api.addMarker(sp.GREEN_CRUISER, x=0, y=3),
                "green",
                "Weymouth",
                0,
                3,
            )
        )
        green_team.append(
            Battleship(  # type:ignore[arg-type]
                api.addMarker(sp.GREEN_BATTLESHIP, x=0, y=5),
                "green",
                "Iron Duke",
                0,
                5,
            )
        )
        list_images = [(Cliff, sp.CLIFF), (Island, sp.ISLAND)]
        count = random.randint(10, 15)

        while count != 0:
            x_rand = random.randint(0, 6)
            y_rand = random.randint(0, 6)
            coordinates = (x_rand, y_rand)
            barrier = random.choice(list_images)
            flag = False

            for obj in red_team:
                if coordinates == (obj.position_x, obj.position_y):
                    flag = True
                    break

            for obj in green_team:
                if coordinates == (obj.position_x, obj.position_y):
                    flag = True
                    break

            for obj in barriers:
                if coordinates == (obj.position_x, obj.position_y):
                    flag = True
                    break

            if flag is True:
                continue

            barriers.append(
                barrier[0](
                    api.addImage(barrier[1], x=x_rand, y=y_rand),
                    x_rand,
                    y_rand,
                )
            )
            count -= 1

    def click(self, api: GameAPI, x: int, y: int) -> None:
        if self.warship is None:
            self.select_warship(x, y)
        else:
            self.warship.move(x, y)
            api.addMessage(
                f"{self.warship.name} moves to {self.letters[x]}{y+1}"
            )
            self.attacks(api)
            self.remove_ship(api)
            self.warship = None
            if self.current_team == "green":
                self.current_team = "red"
            elif self.current_team == "red":
                self.current_team = "green"
            api.addMessage(f"-- {self.current_team} --")

    def select_warship(self, x: int, y: int) -> None:
        for ship_red in red_team:
            ship_red.marker.setSelected(False)
            if (x, y) == (
                ship_red.position_x,
                ship_red.position_y,
            ) and self.current_team == "red":
                self.warship = ship_red

        for ship_green in green_team:
            ship_green.marker.setSelected(False)
            if (x, y) == (
                ship_green.position_x,
                ship_green.position_y,
            ) and self.current_team == "green":
                self.warship = ship_green

        if self.warship is not None:
            self.warship.marker.setSelected(True)

    def attacks(self, api: GameAPI):
        if self.current_team == "red":
            for ship in green_team:
                attack_list = ship.attack()
                for attack in attack_list:
                    api.addMessage(
                        f"{attack[2]} attacks {attack[0]} for {attack[1]} damage"
                    )

        if self.current_team == "green":
            for ship in red_team:
                attack_list = ship.attack()
                for attack in attack_list:
                    api.addMessage(
                        f"{attack[2]} attacks {attack[0]} for {attack[1]} damage"
                    )

    def remove_ship(self, api):
        temp = []
        for ship_g in green_team:
            if ship_g.health_current <= 0:
                ship_g.marker.remove()
                temp.append(ship_g)
                api.addMessage(f"The {ship_g.name} is destroyed")

        for ship_r in red_team:
            if ship_r.health_current <= 0:
                ship_r.marker.remove()
                temp.append(ship_r)
                api.addMessage(f"The {ship_r.name} is destroyed")

        for ship in temp:
            if ship in green_team:
                green_team.remove(ship)
            elif ship in red_team:
                red_team.remove(ship)

        if len(green_team) == 0:
            api.addMessage("The Red team won")
            api.addMessage("The game is over")
        if len(red_team) == 0:
            api.addMessage("The Green team won")
            api.addMessage("The game is over")
