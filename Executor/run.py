from guardian import Guardian
import argparse


def run(app_name, apk_name, testing_objective):
    max_test_step = 30
    guardian = Guardian(app_name , apk_name, testing_objective, "emulator-5554", max_test_step)
    test_case = guardian.genTestCase()
    print(test_case)

if __name__ == "__main__":
    # parse cmdline args, including apk_name, testing_obejctive, and max_test_step
    parser = argparse.ArgumentParser(description='Guardian')
    parser.add_argument('app_name', type=str, help='app name specified in the apk_info.csv')
    parser.add_argument('apk_name', type=str, help='apk name')
    parser.add_argument('testing_objective', type=str, help='testing objective')
    parser.add_argument('max_test_step', type=int, help='max test step')
    args = parser.parse_args()
    
    guardian = Guardian(args.app_name ,args.apk_name, args.testing_objective, "emulator-5554", args.max_test_step)
    test_case = guardian.genTestCase()
    print(test_case)

