=== TEST DATA CREDENTIALS ===

ADMIN:
  Name: Admin User
  Email: admin@example.com
  Password: admin123
  ID: f8a468ff-ecc2-4c24-93b7-a86de7ce15b1

HOSPITALS:
  Hospital 1:
    Name: Hospital 1
    Email: hospital1@example.com
    Password: hospital1
    ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00

  Hospital 2:
    Name: Hospital 2
    Email: hospital2@example.com
    Password: hospital2
    ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7

DOCTORS:
  Doctor 1 (Cardiologist):
    Name: Dr. John Smith
    Email: doctor1@example.com
    Password: doctor1
    ID: d2b372f1-df48-4c2b-a748-a694f432eebb

  Doctor 2 (Neurologist):
    Name: Dr. Sarah Johnson
    Email: doctor2@example.com
    Password: doctor2
    ID: 4a566a32-0c03-49a9-bee5-3068ef4b2ca6

  Doctor 3 (Pediatrician):
    Name: Dr. Michael Williams
    Email: doctor3@example.com
    Password: doctor3
    ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb

  Doctor 4 (Orthopedic Surgeon):
    Name: Dr. Emily Brown
    Email: doctor4@example.com
    Password: doctor4
    ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9

  Doctor 5 (General Practitioner):
    Name: Dr. David Jones
    Email: doctor5@example.com
    Password: doctor5
    ID: 3f694912-1c69-4fb2-b236-35e1655dabdf

PATIENTS:
  Patient User 1:
    Name: Patient User 1
    Email: patient1@example.com
    Password: patient1
    ID: 660e15a0-0d01-4ec6-9dc2-6d197b262b8b
    Associated Patients:
      Patient 1: Alice Smith (Relation: self, ID: 28e8581d-5203-4407-a9ee-c006976976c3)
      Patient 2: Bob Smith (Relation: child, ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)

  Patient User 2:
    Name: Patient User 2
    Email: patient2@example.com
    Password: patient2
    ID: 65e735a5-7e34-482d-a980-67e6a13ed7fd
    Associated Patients:
      Patient 1: Diana Johnson (Relation: self, ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)
      Patient 2: Eva Johnson (Relation: parent, ID: a31aec54-f4e5-40e7-bccd-7e6bf5677387)

  Patient User 3:
    Name: Patient User 3
    Email: patient3@example.com
    Password: patient3
    ID: 2773d15f-4709-4e96-be3f-bf7614489604
    Associated Patients:
      Patient 1: Grace Williams (Relation: self, ID: 59fdbaa4-a5eb-45d5-9f50-3838ee358b1c)
      Patient 2: Henry Williams (Relation: guardian, ID: bb4f4995-349b-4afb-8d1d-1e2c8e7fe7da)

  Patient User 4:
    Name: Patient User 4
    Email: patient4@example.com
    Password: patient4
    ID: c539eae8-66a2-4aa8-a0ac-03ea6012dc05
    Associated Patients:
      Patient 1: Jack Brown (Relation: self, ID: 20648aab-39b0-4135-be8c-87cef9a7a435)
      Patient 2: Kate Brown (Relation: friend, ID: 72ba809d-2d3a-4725-b50e-88dccf841a15)

=== MAPPING INFORMATION ===

Hospital-Doctor Mappings:
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Doctor 'Dr. John Smith' (ID: d2b372f1-df48-4c2b-a748-a694f432eebb)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Doctor 'Dr. Sarah Johnson' (ID: 4a566a32-0c03-49a9-bee5-3068ef4b2ca6)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Doctor 'Dr. Michael Williams' (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb)
  Hospital 'Hospital 2' (ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7) -> Doctor 'Dr. Emily Brown' (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9)
  Hospital 'Hospital 2' (ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7) -> Doctor 'Dr. David Jones' (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf)

Hospital-Patient Mappings:
  Hospital 'Hospital 2' (ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7) -> Patient 'Alice Smith' (ID: 28e8581d-5203-4407-a9ee-c006976976c3)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Patient 'Bob Smith' (ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)
  Hospital 'Hospital 2' (ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7) -> Patient 'Diana Johnson' (ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Patient 'Eva Johnson' (ID: a31aec54-f4e5-40e7-bccd-7e6bf5677387)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Patient 'Grace Williams' (ID: 59fdbaa4-a5eb-45d5-9f50-3838ee358b1c)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Patient 'Henry Williams' (ID: bb4f4995-349b-4afb-8d1d-1e2c8e7fe7da)
  Hospital 'Hospital 2' (ID: 9f9f7f03-8d33-42d4-81bf-2d2d084960c7) -> Patient 'Jack Brown' (ID: 20648aab-39b0-4135-be8c-87cef9a7a435)
  Hospital 'Hospital 1' (ID: 1458ab7b-71fa-4684-90ea-ebde67c9fa00) -> Patient 'Kate Brown' (ID: 72ba809d-2d3a-4725-b50e-88dccf841a15)

Doctor-Patient Mappings:
  Doctor 'Dr. Michael Williams' (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb) -> Patient 'Alice Smith' (ID: 28e8581d-5203-4407-a9ee-c006976976c3)
  Doctor 'Dr. Michael Williams' (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb) -> Patient 'Bob Smith' (ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)
  Doctor 'Dr. David Jones' (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf) -> Patient 'Bob Smith' (ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)
  Doctor 'Dr. Emily Brown' (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9) -> Patient 'Diana Johnson' (ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)
  Doctor 'Dr. David Jones' (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf) -> Patient 'Diana Johnson' (ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)
  Doctor 'Dr. Emily Brown' (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9) -> Patient 'Eva Johnson' (ID: a31aec54-f4e5-40e7-bccd-7e6bf5677387)
  Doctor 'Dr. Emily Brown' (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9) -> Patient 'Grace Williams' (ID: 59fdbaa4-a5eb-45d5-9f50-3838ee358b1c)
  Doctor 'Dr. David Jones' (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf) -> Patient 'Henry Williams' (ID: bb4f4995-349b-4afb-8d1d-1e2c8e7fe7da)
  Doctor 'Dr. Sarah Johnson' (ID: 4a566a32-0c03-49a9-bee5-3068ef4b2ca6) -> Patient 'Jack Brown' (ID: 20648aab-39b0-4135-be8c-87cef9a7a435)
  Doctor 'Dr. Michael Williams' (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb) -> Patient 'Kate Brown' (ID: 72ba809d-2d3a-4725-b50e-88dccf841a15)

Chat Sessions:
  Chat ID: 38d82e25-94cf-43bc-a589-9ca444ffb9b7
    Doctor: Dr. Michael Williams (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb)
    Patient: Alice Smith (ID: 28e8581d-5203-4407-a9ee-c006976976c3)

  Chat ID: 882c2d2a-44e2-4ec1-8bd3-191b76604d2a
    Doctor: Dr. Michael Williams (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb)
    Patient: Bob Smith (ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)

  Chat ID: 0ce0483e-d0e1-4442-b1dd-e0544186276d
    Doctor: Dr. David Jones (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf)
    Patient: Bob Smith (ID: bd92fe57-afcd-4a54-888e-68f2ec46a039)

  Chat ID: 584fcd24-c240-45fd-b407-f8f01ba485d0
    Doctor: Dr. Emily Brown (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9)
    Patient: Diana Johnson (ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)

  Chat ID: ad16ad1c-260b-4fd2-85a4-3e5c27150a5f
    Doctor: Dr. David Jones (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf)
    Patient: Diana Johnson (ID: e988e4c7-ad52-4161-87f6-a86eca3b8135)

  Chat ID: 15a41014-a5da-4c51-924b-16ffde6073d5
    Doctor: Dr. Emily Brown (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9)
    Patient: Eva Johnson (ID: a31aec54-f4e5-40e7-bccd-7e6bf5677387)

  Chat ID: 46afe529-72dd-433c-9aa5-31e428bc9bc3
    Doctor: Dr. Emily Brown (ID: 6fb7bd98-3fbc-49d0-9880-231eb2d888c9)
    Patient: Grace Williams (ID: 59fdbaa4-a5eb-45d5-9f50-3838ee358b1c)

  Chat ID: 57eedcbe-ee87-499d-a4a6-e2c84edfece0
    Doctor: Dr. David Jones (ID: 3f694912-1c69-4fb2-b236-35e1655dabdf)
    Patient: Henry Williams (ID: bb4f4995-349b-4afb-8d1d-1e2c8e7fe7da)

  Chat ID: 6d1f1fc2-c5cb-47aa-a2b8-09125fbcafc1
    Doctor: Dr. Sarah Johnson (ID: 4a566a32-0c03-49a9-bee5-3068ef4b2ca6)
    Patient: Jack Brown (ID: 20648aab-39b0-4135-be8c-87cef9a7a435)

  Chat ID: a7ed51cb-3ea1-4df9-95e2-ecb183f3e3b3
    Doctor: Dr. Michael Williams (ID: e10f677c-38c4-4bec-840c-a340bbc8b1cb)
    Patient: Kate Brown (ID: 72ba809d-2d3a-4725-b50e-88dccf841a15)