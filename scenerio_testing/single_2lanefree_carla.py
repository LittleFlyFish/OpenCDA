# -*- coding: utf-8 -*-
"""
Scenario testing: merging vehicle joining a platoon in the customized 2-lane freeway simplified map sorely with carla
"""
# Author: Runsheng Xu <rxx3386@ucla.edu>
# License: MIT

import argparse
import os

import carla

import scenerio_testing.utils.sim_api as sim_api
import scenerio_testing.utils.customized_map_api as map_api

# todo: PlatoonWorld is ugly
from core.application.platooning.platooning_world import PlatooningWorld
from scenerio_testing.utils.yaml_utils import load_yaml


def arg_parse():
    parser = argparse.ArgumentParser(description="Platooning Joining Settings")
    parser.add_argument("--config_yaml", required=True, type=str, help='corresponding yaml file of the testing')
    parser.add_argument("--record", action='store_true', help='whether to record playfile')

    opt = parser.parse_args()
    return opt


def main():
    try:
        # first define the path of the yaml file and 2lanefreemap file
        opt = arg_parse()
        scenario_params = load_yaml(opt.config_yaml)
        current_path = os.path.dirname(os.path.realpath(__file__))
        xodr_path = os.path.join(current_path,
                                 '../assets/2lane_freeway_simplified/map_v7.4_smooth_curve.xodr')

        # create simulation world
        simulation_config = scenario_params['world']
        client, world, carla_map, origin_settings = sim_api.createSimulationWorld(simulation_config, xodr_path)

        if opt.record:
            client.start_recorder("platoon_joining_town06_carla.log", True)

        # create background traffic in carla
        traffic_manager, bg_veh_list = sim_api.createTrafficManager(client, world,
                                                                    scenario_params['carla_traffic_manager'])

        # todo: temporary
        platooning_world = PlatooningWorld()
        single_cav_list = sim_api.createVehicleManager(world, scenario_params, ['single'], platooning_world,
                                                       carla_map, map_api.spawn_helper_2lanefree)

        spectator = world.get_spectator()
        # run steps
        while True:
            world.tick()
            transform = single_cav_list[0].vehicle.get_transform()
            spectator.set_transform(carla.Transform(transform.location + carla.Location(z=50),
                                                    carla.Rotation(pitch=-90)))

            for i, single_cav in enumerate(single_cav_list):
                single_cav.update_info(platooning_world)
                control = single_cav.run_step()
                single_cav.vehicle.apply_control(control)

    finally:
        if opt.record:
            client.stop_recorder()

        world.apply_settings(origin_settings)

        for v in single_cav_list:
            v.destroy()
        for v in bg_veh_list:
            v.destroy()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' - Exited by user.')