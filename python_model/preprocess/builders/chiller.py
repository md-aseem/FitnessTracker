import pandas as pd
from pathlib import Path
from python_model.preprocess.properties import InputConfig, ChillerSpecs

def build_chiller_specs(input_config: InputConfig, library_data) -> ChillerSpecs:
    """
    The code to build chiller config.
    The code needs improvement. There is a lot of hardcoding right now.
    """
    chiller_model = input_config.chiller_model
    quantum = input_config.quantum

    is_envicool = 'envicool_55kW' in chiller_model
    if is_envicool and int(quantum) == '2p0':
        chiller_curves_dir = library_data['chillers']['envicool_q2_55kw']['chiller_curves_dir']

        low_temp = pd.read_csv(Path(__file__).parent.parent.parent / chiller_curves_dir / "envicool_55kw_18c.csv")
        low_temp['temp'] = 18

        high_temp = pd.read_csv(Path(__file__).parent.parent.parent / chiller_curves_dir / "envicool_55kw_23c.csv")
        high_temp['temp'] = 23

        chiller_curves_df = pd.concat([low_temp, high_temp], ignore_index=True)

    else:
        chiller_curves_df = pd.DataFrame()

    chiller_data = library_data['chillers']['envicool_q2_55kw']

    return ChillerSpecs(
        chiller_model=chiller_model,
        chiller_noise_kit=input_config.chiller_noise_kit,
        chiller_curves_df=chiller_curves_df,
        battery_sensitivity= chiller_data['battery_sensitivity'],
        inverter_sensitivity= chiller_data['inverter_sensitivity'],
        battery_temp_target_C=chiller_data['battery_temp_target_C'],
        inverter_temp_target_C=chiller_data['inverter_temp_target_C'],
        electronics_aux_power=chiller_data['electronics_aux_power'],
        pcs_pump_power_per_pcnt=chiller_data['pcs_pump_power_per_pcnt'],
        bat_pump_power_per_prcnt=chiller_data['bat_pump_power_per_prcnt'],
        fan_aux_power_per_pcnt=chiller_data['fan_aux_power_per_pcnt'],
        bat_volume_flow_rate_per_prcnt=chiller_data['bat_volume_flow_rate_per_prcnt'],
        pcs_volume_flow_rate_per_prcnt=chiller_data['pcs_volume_flow_rate_per_prcnt']
    )
