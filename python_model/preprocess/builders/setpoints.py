from python_model.preprocess.properties import SetPoints

def build_setpoints(input_config):

    setpoints = SetPoints(chiller_setpoint=input_config.chiller_setpoint,
                          battery_cool_target=input_config.battery_cool_target,
                          battery_cool_min=input_config.battery_cool_min,
                          battery_cool_exit=input_config.battery_cool_exit,
                          b_coolant_target=input_config.b_coolant_target,
                          battery_heat_min=input_config.battery_heat_min,
                          battery_heat_target=input_config.battery_heat_target,
                          battery_heat_max=input_config.battery_heat_max,
                          battery_heat_exit=input_config.battery_heat_exit
                          )
    return setpoints