import requests
import random
from faker import Faker
from constants import (
    API_BASE_URL,
    ENDPOINT_PATIENTS,
    GENDER_CHOICES,
    MAX_LENGTH_NATIONAL_ID,
    SEED_FAKER_LOCALE,
    SEED_PATIENT_EXTERNAL_ID_PREFIX,
    SEED_PATIENT_EXTERNAL_ID_MIN,
    SEED_PATIENT_EXTERNAL_ID_MAX,
    SEED_PATIENT_AGE_MIN,
    SEED_PATIENT_AGE_MAX,
    SEED_INSURANCE_CARD_PREFIX,
    SEED_INSURANCE_CARD_DIGITS,
    SEED_DEFAULT_PATIENT_COUNT,
    SEED_PROGRESS_INTERVAL,
)

fake = Faker(SEED_FAKER_LOCALE)  # Sử dụng locale Việt Nam để tên và địa chỉ thực tế
API_URL = f"{API_BASE_URL}{ENDPOINT_PATIENTS}"


def generate_patient_data():
    gender = random.choice(GENDER_CHOICES)
    # Tạo mã bệnh nhân giả lập BN-XXXXX
    external_id = f"{SEED_PATIENT_EXTERNAL_ID_PREFIX}-{fake.unique.random_int(min=SEED_PATIENT_EXTERNAL_ID_MIN, max=SEED_PATIENT_EXTERNAL_ID_MAX)}"

    # Tạo số CCCD giả lập (12 số)
    national_id = "".join(
        [str(random.randint(0, 9)) for _ in range(MAX_LENGTH_NATIONAL_ID)]
    )

    return {
        "patient_external_id": external_id,
        "national_id": national_id,
        "full_name": fake.name(),
        "gender": gender,
        "birth_date": fake.date_of_birth(
            minimum_age=SEED_PATIENT_AGE_MIN, maximum_age=SEED_PATIENT_AGE_MAX
        ).isoformat(),
        "address": fake.address().replace("\n", ", "),
        "phone": fake.phone_number(),
        "insurance_card_no": f"{SEED_INSURANCE_CARD_PREFIX}{fake.random_number(digits=SEED_INSURANCE_CARD_DIGITS)}",
    }


def seed_patients(n=SEED_DEFAULT_PATIENT_COUNT):
    print(f"🚀 Bắt đầu sinh {n} dữ liệu bệnh nhân...")
    success_count = 0

    for i in range(n):
        payload = generate_patient_data()
        try:
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                success_count += 1
                if success_count % SEED_PROGRESS_INTERVAL == 0:
                    print(f"✅ Đã tạo thành công {success_count}/{n} bệnh nhân")
            else:
                print(f"❌ Lỗi tại bệnh nhân thứ {i+1}: {response.text}")
        except Exception as e:
            print(f"‼️ Không thể kết nối tới API: {e}")
            break

    print(f"\n✨ Hoàn thành! {success_count} bệnh nhân đã được đưa vào hệ thống.")
    print("👉 Hãy kiểm tra RabbitMQ Dashboard để thấy các sự kiện đang chờ xử lý.")



def seed_complex_workflow(count=10):
    print(f"Bắt đầu seed sinh lực dữ liệu (encounters, conditions, medication requests...)")
    try:
        # Seeding encounters
        res_enc = requests.post(f"{API_BASE_URL}/test/seed-encounter/{count}")
        
        # Seeding conditions
        res_cond = requests.post(f"{API_BASE_URL}/test/seed-condition/{count}")

        # Seeding medications
        res_med = requests.post(f"{API_BASE_URL}/test/seed-medication/{count}")
        print(f"Hoàn thành seed các thực thể y tế.")
    except Exception as e:
        print(f"Lỗi khi seed complex workflow: {e}")

if __name__ == "__main__":
    seed_patients(100)  # Thử nghiệm với 100 bệnh nhân
    seed_complex_workflow(50)
