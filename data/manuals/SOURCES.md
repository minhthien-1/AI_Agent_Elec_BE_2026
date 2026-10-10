# Elec-Agent — Source Registry (P1-1)

Ngày kiểm tra URL nguồn: 2026-10-10. Cập nhật registry: 2026-10-11. Theo xác nhận của người thực hiện, các tài liệu đã được mở bằng trình đọc PDF và review nội dung; trạng thái bên dưới được cập nhật theo báo cáo đó, không phải kết quả kiểm tra trực tiếp thư mục máy tính từ phía trợ lý. SHA-256 trước đó phát hiện M002 và bản manual M007 cũ giống hệt nhau. M007 hiện được đăng ký là Hướng dẫn thiết lập nhanh chính thức của LG tại `files/manuals/refrigerators/M007_lg_LFD61BLGA_quick_setup_vi.pdf`. Trước khi tuyên bố P1-1 hoàn tất, cần chạy lại script kiểm tra và SHA-256 trên bộ file hiện tại để xác nhận đúng 30 file, M007 mới tồn tại và không còn bản trùng byte-for-byte chưa xử lý.

## Quy tắc trạng thái

- `TODO_DOWNLOAD`: chưa có file tại Local File.
- `DOWNLOADED`: file đã được lưu đúng đường dẫn nhưng chưa rà soát nội dung/model.
- `REVIEWED`: đã mở file, xem tiêu đề/nội dung, xác minh model nếu có và kiểm tra file không phải trang lỗi.
- Trạng thái `REVIEWED` trong phiên bản registry này phản ánh báo cáo review của người thực hiện ngày 2026-10-11. Nếu có hàng nào chưa thực sự được kiểm tra, hạ riêng hàng đó về `DOWNLOADED` hoặc `TODO_DOWNLOAD` cho đúng thực tế.
- Với bài viết web/FAQ, lưu trang bằng trình duyệt Print → Save as PDF và ghi rõ đó là bản lưu trang web; đừng mô tả nó như manual nhà sản xuất.
- Không chỉnh PDF có bản quyền để phân phối, không commit/redistribute bản gốc lên repo công khai nếu chưa xác nhận được quyền.

## Thư mục đích

```text
data/manuals/
├── SOURCES.md
└── files/
    ├── manuals/
    │   ├── washing_machines/
    │   ├── refrigerators/
    │   ├── air_conditioners/
    │   ├── freezers/              # tạo thêm cho M006
    │   └── water_heaters/         # để dành; danh sách hiện tại chưa có manual nước nóng
    ├── warranty/
    ├── technical_guides/
    └── safety/
```

## Registry

| ID | Category | Title | Brand / Model | Language | Source URL | Local File (relative to data/manuals/) | Accessed On | Status | Download/Review notes |
|---|---|---|---|---|---|---|---|---|---|
| M001 | Manual | User Manual — máy giặt cửa trên 14 kg | Samsung WA14CG5886BDSV | VI | https://www.samsung.com/vn/support/model/WA14CG5886BDSV/ | files/manuals/washing_machines/M001_samsung_WA14CG5886BDSV_manual_vi.pdf | 2026-10-10 | REVIEWED | Tải mục User Manual / Hướng dẫn sử dụng; chọn Vietnamese. Trang Samsung đang có PDF tiếng Việt cho model này. |
| M002 | Manual | Sách hướng dẫn sử dụng — tủ lạnh French Door 571L | LG LFD58BLMA | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-LFD58BLMA.AEPPEVN/ | files/manuals/refrigerators/M002_lg_LFD58BLMA_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Tải xuống tài liệu hướng dẫn → Sách hướng dẫn sử dụng → Vietnamese/PDF → Download. |
| M003 | Manual | Sách hướng dẫn sử dụng — tủ lạnh French Door 510L | LG F51EG | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-F51EG.ADMPEVN/ | files/manuals/refrigerators/M003_lg_F51EG_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Sách hướng dẫn sử dụng; chọn file PDF tiếng Việt, không chọn Online Manual HTML nếu muốn lưu PDF. |
| M004 | Manual | Sách hướng dẫn sử dụng — tủ lạnh ngăn đá trên 266L | LG LTB26SVM | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-LTB26SVM.APYPEVN/ | files/manuals/refrigerators/M004_lg_LTB26SVM_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Sách hướng dẫn sử dụng → Vietnamese → Download. |
| M005 | Manual | Sách hướng dẫn sử dụng — điều hòa | LG IDC09M1N | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-IDC09M1N.ATYGEVH/ | files/manuals/air_conditioners/M005_lg_IDC09M1N_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Sách hướng dẫn sử dụng → PDF → Vietnamese → Download. Có thể có Online Manual riêng; ưu tiên PDF. |
| M006 | Manual | Sách hướng dẫn sử dụng — tủ đông 165L | LG LOF16BGM | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-LOF16BGM.ABNPEVN/ | files/manuals/freezers/M006_lg_LOF16BGM_manual_vi.pdf | 2026-10-10 | REVIEWED | Tạo thêm thư mục manuals/freezers; tìm Sách hướng dẫn sử dụng → Vietnamese/PDF → Download. |
| M007 | Quick-start guide | Hướng dẫn thiết lập nhanh — tủ lạnh French Door 607L | LG LFD61BLGA | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-LFD61BLGA/ | files/manuals/refrigerators/M007_lg_LFD61BLGA_quick_setup_vi.pdf | 2026-10-10 | REVIEWED | Theo báo cáo review ngày 2026-10-11: đã thay bản manual trùng M002 bằng Hướng dẫn thiết lập nhanh tiếng Việt cho LG LFD61BLGA. Đường dẫn hiện đăng ký là `M007_lg_LFD61BLGA_quick_setup_vi.pdf`; cần xác nhận script và hash trên thư mục hiện tại trước khi chốt P1-1. |
| M008 | Manual | Sách hướng dẫn sử dụng — tủ lạnh ngăn đá trên 394L | LG GN-D392BLA | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-GN-D392BLA/ | files/manuals/refrigerators/M008_lg_GN-D392BLA_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Sách hướng dẫn sử dụng → Vietnamese/PDF → Download. |
| M009 | Manual | Sách hướng dẫn sử dụng — máy giặt sấy cửa trước 9kg | LG FB1209D5W | VI | https://www.lg.com/vn/tro-giup/ho-tro-san-pham/cs-FB1209D5W/ | files/manuals/washing_machines/M009_lg_FB1209D5W_manual_vi.pdf | 2026-10-10 | REVIEWED | Tìm mục Sách hướng dẫn sử dụng → Vietnamese/PDF → Download. |
| G001 | Guide | Hướng dẫn sử dụng tủ lạnh Panasonic | Panasonic — nhiều dòng tủ lạnh | VI | https://www.panasonic.com/vn/support/user-manual-fridge.html | files/technical_guides/G001_panasonic_fridge_usage_guide.pdf | 2026-10-10 | REVIEWED | Đây là hướng dẫn web theo dòng sản phẩm, không phải manual riêng một model. Lưu PDF bằng Ctrl+P → Save as PDF và ghi rõ là bản lưu trang web. |
| W001 | Warranty | Chính sách thời hạn bảo hành sản phẩm | Panasonic Việt Nam | VI/EN | https://www.panasonic.com/vn/support/product-warranty-period.html | files/warranty/W001_panasonic_warranty_period_2026.pdf | 2026-10-10 | REVIEWED | Ưu tiên tải PDF chính sách trên trang chính thức. Trang được kiểm tra hiển thị hiệu lực 28/07/2026–31/03/2027; khi tải, ghi ngày hiệu lực/phiên bản thực tế. |
| W002 | Warranty | Điều kiện bảo hành | Panasonic Việt Nam | VI | https://www.panasonic.com/vn/support/warrantyterms.html | files/warranty/W002_panasonic_warranty_terms.pdf | 2026-10-10 | REVIEWED | Nếu trang không có PDF tải riêng, Ctrl+P → Save as PDF; ghi đây là bản lưu trang chính sách. |
| T001 | Technical | Máy giặt phát ra tiếng ồn | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/washing-machine/noise | files/technical_guides/T001_toshiba_washer_noise.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T002 | Technical | Cách bảo dưỡng máy giặt | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/washing-machine/maintenance | files/technical_guides/T002_toshiba_washer_maintenance.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T003 | Technical | Tủ lạnh phát ra tiếng ồn | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/refrigerator/noise | files/technical_guides/T003_toshiba_fridge_noise.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T004 | Technical | Tổng quan cách bảo dưỡng tủ lạnh | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/refrigerator/maintenance-overview | files/technical_guides/T004_toshiba_fridge_maintenance.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T005 | Technical | Tủ lạnh không hoạt động? | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/refrigerator/not-working | files/technical_guides/T005_toshiba_fridge_not_working.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T006 | Technical | Đây không phải là hiện tượng hư hỏng (điều hòa) | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/air-conditioner/not-a-malfunction | files/technical_guides/T006_toshiba_ac_normal_behaviors.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. Hữu ích để phân biệt hiện tượng bình thường với sự cố. |
| T007 | Technical | Bảo dưỡng và vệ sinh máy điều hòa | Toshiba | VI | https://www.toshiba-lifestyle.com/vn/support/faq/air-conditioner/maintenance-cleaning | files/technical_guides/T007_toshiba_ac_maintenance.pdf | 2026-10-10 | REVIEWED | Mở bài FAQ rồi Ctrl+P → Save as PDF. |
| T008 | Technical | Hướng dẫn các bước bảo dưỡng bình nóng lạnh đúng cách | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/meo-va-giai-phap/huong-dan-bao-duong-binh-nong-lanh-tai-nha | files/technical_guides/T008_ariston_water_heater_maintenance.pdf | 2026-10-10 | REVIEWED | Mở bài chính thức rồi Ctrl+P → Save as PDF. Khi dùng cho AI, rà soát kỹ thao tác bảo trì bên trong thiết bị. |
| T009 | Technical | Cách sửa bình nóng lạnh không nóng hiệu quả, an toàn | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/meo-va-giai-phap/binh-nong-lanh-khong-nong-nguyen-nhan-va-cach-khac-phuc | files/technical_guides/T009_ariston_water_heater_not_heating.pdf | 2026-10-10 | REVIEWED | Mở bài chính thức rồi Ctrl+P → Save as PDF. Không biến mọi chỉ dẫn sửa chữa thành thao tác DIY cho người phổ thông. |
| T010 | Technical | Máy nước nóng quá nóng: nguyên nhân và khắc phục | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/meo-va-giai-phap/cach-xu-ly-may-nuoc-nong-qua-nong-cac-buoc-an-toan-va-bien-phap-phong-ngua | files/technical_guides/T010_ariston_water_heater_overheating.pdf | 2026-10-10 | REVIEWED | Mở bài chính thức rồi Ctrl+P → Save as PDF. |
| T011 | Technical | Máy nước nóng trực tiếp có an toàn không? Cách sử dụng đúng | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/meo-va-giai-phap/su-dung-may-nuoc-nong-truc-tiep-co-an-toan-khong | files/technical_guides/T011_ariston_instant_heater_safety.pdf | 2026-10-10 | REVIEWED | Mở bài chính thức rồi Ctrl+P → Save as PDF. |
| T012 | Technical | 10 lỗi thường gặp và cách sửa máy nước nóng hiệu quả | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/meo-va-giai-phap/nhung-luu-y-can-biet-khi-sua-binh-nuoc-nong-tai-nha | files/technical_guides/T012_ariston_water_heater_common_faults.pdf | 2026-10-10 | REVIEWED | Mở bài chính thức rồi Ctrl+P → Save as PDF. Giữ lại cảnh báo tắt nguồn/gọi chuyên viên nếu bài có nêu. |
| T013 | Technical | Bảo trì máy nước nóng năng lượng mặt trời | Ariston | VI | https://www.ariston.com/vi-vn/the-comfort-way/tips-and-tricks/bao-tri-may-nuoc-nong-nang-luong-mat-troi-huong-dan-huu-ich-de-duy-tri-he-thong-van-hanh-hieu-qua/ | files/technical_guides/T013_ariston_solar_heater_maintenance.pdf | 2026-10-10 | REVIEWED | URL đã kiểm tra chuyển hướng tới bài Ariston hiện hành về bảo trì. Mở bài rồi Ctrl+P → Save as PDF; đánh dấu những thao tác yêu cầu kỹ thuật viên. |
| S001 | Safety | Quá tải điện trong gia đình: nhận biết sớm để phòng ngừa cháy nổ | EVN | VI | https://www.evn.com.vn/d/vi-VN/news/Qua-tai-dien-trong-gia-dinh-Nhan-biet-som-de-phong-ngua-chay-no-60-3570-509328 | files/safety/S001_evn_home_electrical_overload.pdf | 2026-10-10 | REVIEWED | Mở bài EVN rồi Ctrl+P → Save as PDF. |
| S002 | Safety | Sử dụng điện trong gia đình: lưu ý phòng ngừa sự cố | EVN | VI | https://www.evn.com.vn/d/vi-VN/news/Su-dung-dien-trong-gia-dinh-Nhung-luu-y-de-phong-ngua-su-co-60-3563-509184 | files/safety/S002_evn_home_electrical_safety.pdf | 2026-10-10 | REVIEWED | Mở bài EVN rồi Ctrl+P → Save as PDF. |
| S003 | Safety | Nhận diện sớm nguy cơ mất an toàn điện trong gia đình | EVN | VI | https://www.evn.com.vn/d/vi-VN/news/Chuyen-gia-chi-cach-nhan-dien-som-nguy-co-mat-an-toan-dien-trong-gia-dinh-60-2021-508466 | files/safety/S003_evn_warning_signs_electrical_danger.pdf | 2026-10-10 | REVIEWED | Mở bài EVN rồi Ctrl+P → Save as PDF. Nội dung có ghi được lược dịch từ EMA Singapore; giữ attribution nếu trích xuất. |
| S004 | Safety | Nghỉ lễ 2/9: Làm gì để an toàn điện khi vắng nhà? | EVN | VI | https://www.evn.com.vn/d/vi-VN/news/Nghi-le-29-Lam-gi-de-an-toan-dien-khi-vang-nha-60-2021-509433 | files/safety/S004_evn_electrical_safety_away_from_home.pdf | 2026-10-10 | REVIEWED | Mở bài EVN rồi Ctrl+P → Save as PDF. |
| S005 | Safety | Sử dụng điện an toàn cần bắt đầu từ nhận thức đúng về trách nhiệm | EVN | VI | https://www.evn.com.vn/d/vi-VN/news/Su-dung-dien-an-toan-can-bat-dau-tu-nhan-thuc-dung-ve-trach-nhiem-60-2021-502455 | files/safety/S005_evn_safe_electricity_responsibility.pdf | 2026-10-10 | REVIEWED | Mở bài EVN rồi Ctrl+P → Save as PDF. |

## Tải và kiểm tra

### Manual M001–M009

1. Mở Source URL của từng dòng trong trình duyệt.
2. Trên trang sản phẩm, xác minh model hiển thị trùng với cột Brand / Model.
3. Mở `Sách hướng dẫn sử dụng` / `User Manual`, chọn ngôn ngữ `Vietnamese` nếu có, rồi bấm tải file PDF. Với trang Samsung/LG, ưu tiên file manual được hãng cung cấp; không dùng trang HTML sản phẩm làm manual.
4. Lưu file với đúng tên và đúng thư mục từ cột Local File. M006 là tủ đông nên lưu trong `manuals/freezers/`; hãy tạo folder này nếu chưa có.
5. Mở PDF và kiểm tra model, ngôn ngữ, trang đầu và vài trang nội dung. Chỉ sau đó đổi `TODO_DOWNLOAD` → `DOWNLOADED` → `REVIEWED` khi đạt yêu cầu.
6. Riêng M007: registry hiện trỏ tới `M007_lg_LFD61BLGA_quick_setup_vi.pdf`, là Hướng dẫn thiết lập nhanh tiếng Việt trên trang hỗ trợ LG LFD61BLGA, khác với sách hướng dẫn sử dụng từng trùng M002. Trạng thái `REVIEWED` phản ánh xác nhận của người thực hiện; vẫn cần kiểm tra lần cuối file hiện tại tồn tại đúng đường dẫn và chạy hash để xác nhận không còn bản sao trùng.

### G001, W001–W002, T001–T013, S001–S005

1. Mở trang nguồn chính thức và kiểm tra tiêu đề/đơn vị phát hành.
2. Nếu có nút tải PDF riêng, tải PDF gốc. Nếu đây là bài web không có PDF tải riêng, dùng `Ctrl+P` → `Save as PDF` và lưu ở đúng `Local File`.
3. Nếu trang bị chuyển hướng, không truy cập được, hoặc nội dung thay đổi, cập nhật URL/ghi chú dựa theo trang cuối cùng thật sự mở được; không đánh dấu review khi chưa kiểm tra.
4. Với W001, ghi lại ngày hiệu lực trên chính sách bảo hành khi tải; đây là loại tài liệu có thể thay đổi theo thời gian.
5. Với T008–T013 về máy nước nóng, đánh dấu các hướng dẫn đụng đến điện, áp suất, tháo lắp hay làm việc trên cao để nhóm Safety rà soát trước khi đưa nội dung vào RAG cho người phổ thông.
6. Với S003, giữ attribution tới EMA Singapore nếu trích xuất vì bài EVN nêu nội dung được lược dịch từ nguồn đó.

## Kiểm tra số lượng và PDF từ PowerShell

Chạy tại thư mục gốc repository. Đoạn này đếm file PDF dưới toàn bộ thư mục con:

```powershell
$files = Get-ChildItem .\data\manuals\files -Recurse -File -Filter *.pdf
"PDF count: $($files.Count)"
$files | Select-Object FullName, Length | Format-Table -AutoSize
```

Đích là 30 file PDF (mỗi ID tương ứng đúng một file). Đếm đủ không đồng nghĩa nội dung đã đúng: mở từng file, so sánh tên/model, kiểm tra file không rỗng và không phải trang lỗi HTML lưu nhầm thành PDF.

Kiểm tra chữ ký PDF:

```powershell
Get-ChildItem .\data\manuals\files -Recurse -File -Filter *.pdf | ForEach-Object {
    $stream = [System.IO.File]::OpenRead($_.FullName)
    try {
        $buffer = New-Object byte[] 5
        [void]$stream.Read($buffer, 0, 5)
        $signature = [System.Text.Encoding]::ASCII.GetString($buffer)
    } finally { $stream.Dispose() }
    [PSCustomObject]@{ Name = $_.Name; ValidPDF = ($signature -eq "%PDF-"); SizeKB = [math]::Round($_.Length / 1KB, 1) }
} | Format-Table -AutoSize
```

## P1-1 DONE khi

- Có đủ 30 file tài liệu thực tế, duy nhất, mở và đọc được.
- Mỗi file nằm đúng thư mục và tên khớp cột Local File.
- Mỗi dòng có URL nguồn chính xác, tên/tiêu đề, brand/model nếu có, ngôn ngữ và trạng thái đã rà soát.
- Không có manual sai model hoặc file lỗi giả dạng PDF.
- Nội dung rủi ro cao được đánh dấu để rà soát an toàn trước khi dùng trong RAG.
- Đã xem xét quyền lưu trữ/chia sẻ trước khi đưa file gốc lên Git.


## Kiểm tra file trùng lặp

Chạy từ thư mục gốc repository. Lệnh sẽ in ra các nhóm có nội dung giống hệt nhau theo SHA-256; không có kết quả nghĩa là chưa phát hiện file trùng byte-for-byte.

```powershell
Get-ChildItem .\data\manuals\files -Recurse -File -Filter *.pdf |
    Get-FileHash -Algorithm SHA256 |
    Group-Object Hash |
    Where-Object { $_.Count -gt 1 } |
    ForEach-Object {
        Write-Host "`nDUPLICATE HASH: $($_.Name)"
        $_.Group | Select-Object Path, Hash | Format-Table -AutoSize
    }
```

Nếu hai file có cùng hash, đừng tự động xóa file. M002 (LFD58BLMA) và bản manual M007 cũ đã trùng byte-for-byte. Để tránh tính một bản sao là hai tài liệu riêng, M007 được đăng ký thành Hướng dẫn thiết lập nhanh PDF tiếng Việt mà trang hỗ trợ LFD61BLGA liệt kê riêng. Theo xác nhận của người thực hiện, tài liệu đã được mở và review; hãy chạy lại kiểm tra hash trên thư mục hiện tại để chắc chắn bản manual cũ đã được thay/xóa và không còn nhóm trùng chưa xử lý.

## Nhật ký review từng tài liệu

Sau khi kiểm tra, chỉ sửa đúng hàng tương ứng:

- `REVIEWED` nghĩa là PDF mở được, tiêu đề/ngôn ngữ đúng, model được xác minh nếu áp dụng, trang không lỗi và nội dung đọc được. Trạng thái hiện tại được cập nhật theo báo cáo của người thực hiện; điều chỉnh từng hàng nếu lần kiểm tra thực tế cho kết quả khác.
- Nếu file mở được nhưng chưa khớp model/ngôn ngữ hoặc có nghi vấn, giữ `DOWNLOADED` và ghi rõ vấn đề ở cột `Download/Review notes`.
- Nếu thiếu file, đổi về `TODO_DOWNLOAD`; nếu tệp không phải PDF hoặc tải nhầm trang lỗi, sửa nguồn/tải lại trước khi đánh dấu review.
- Với `G001`, `W002`, `T001–T013`, `S001–S005` là bản in từ trang web nếu không có PDF gốc, hãy ghi rõ trong ghi chú `Web page saved as PDF`, đồng thời kiểm tra tên bài/đơn vị phát hành.
- Với `W001`, ghi ngày hiệu lực thực tế hiển thị trên tài liệu đã lưu; không dựa riêng vào ngày kiểm tra URL.
