# Báo Cáo Lab 7: Embedding & Vector Store

**Họ tên:** Vương Hoàng Giang
**Nhóm:** [Tên nhóm]
**Ngày:** 10/4/2026

---

## 1. Warm-up (5 điểm)

### Cosine Similarity (Ex 1.1)

**High cosine similarity nghĩa là gì?**
> *Trong các mô hình AI, các đoạn văn bản được chuyển thành các chuỗi số là vector nhúng (embeddings). Khi hai đoạn văn bản có độ tương đồng cao (cosine giữa 2 vector cao gần bằng 1) nghĩa là hai đoạn văn bản đó có cùng chủ đề, ý nghĩa, ngữ cảnh ngay cả khi chúng không sử dụng các từ vựng giống hệt nhau.*

**Ví dụ HIGH similarity:**
- Sentence A: Con chó đen đang đuổi theo quả bóng trên bãi cỏ.
- Sentence B: Con cún sẫm màu đang chạy theo đồ chơi ngoài sân
- Tại sao tương đồng: Mặc dù sử dụng ngữ cảnh khác nhau, mô hình ngôn ngữ hiểu rằng cả hai đều miêu tả cùng chủ thể, hành động và ngữ cảnh. Các vector của chúng nằm rất gần nhau, tạo ra góc rất nhỏ và độ tương đồng cosine gần bằng 1.

**Ví dụ LOW similarity:**
- Sentence A: Con chó đen đang đuổi theo quả bóng trên bãi cỏ.
- Sentence B: Giá xăng dầu sẽ tăng vào tháng tới.
- Tại sao khác: Hai câu này thuộc vào hai lĩnh vực hoàn toàn khác biệt. Hai vector của chúng sẽ chỉ về hai hướng rất xa nhau, mang lại độ tương đồng cosine gần bằng 0 (hoặc thậm chí là gần bằng -1).

**Tại sao cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings?**
> *Thông thường, một số văn bản có độ dài khác nhau nhưng về tầng ý nghĩa lại giống nhau. Nếu ta đo khoảng cách giữa 2 vector các đoạn văn bản này bằng Euclidean distance sẽ khiến hệ thống đánh giá sai rằng hai đoạn văn bản này không liên quan. Ngược lại nếu dùng cosine similarity, hệ thống sẽ chỉ quan tâm đến hướng của chúng, nếu hai vector đều chỉ cùng 1 chủ đề thì góc của chúng sẽ rất nhỏ, nên độ tương đồng cao. Điều này khiến nó trở thành thước đo được ưu tiên hơn Euclidean distance cho text embeddings*

### Chunking Math (Ex 1.2)

**Document 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Phần văn bản thực tế mỗi chunk "tiến lên" (bước nhảy/stride) là 500 - 50 = 450 ký tự. Tổng số chunk là: $\lceil\frac{10000 - 50}{450}\rceil = \lceil\frac{9950}{450}\rceil = \lceil22.11\rceil$
> *Đáp án: 23 chunks*

**Nếu overlap tăng lên 100, chunk count thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**
> *Nếu overlap tăng lên 100, bước nhảy sẽ ngắn lại (còn 400), khiến tổng số chunk tăng lên thành 25 (vì $\lceil\frac{10000 - 100}{400}\rceil = \lceil24.75\rceil = 25$). Việc tăng overlap giúp bảo toàn ngữ cảnh tốt hơn, đảm bảo các câu hoặc khái niệm nằm ở ranh giới giữa các chunk không bị cắt đứt, giúp mô hình không bị mất thông tin khi truy xuất.*

---

## 2. Document Selection — Nhóm (10 điểm)

### Domain & Lý Do Chọn

**Domain:** Vietnamese Cooking Recipes 

**Tại sao nhóm chọn domain này?**
> *Các tài liệu công thức nấu ăn có cấu trúc rất rõ ràng, bao gồm các phần cố định như Giới thiệu, Nguyên liệu và Các bước thực hiện. Cấu trúc này rất phù hợp để đánh giá xem chiến lược chunking có bảo toàn được trọn vẹn ngữ cảnh của một bước nấu hay danh sách nguyên liệu hay không. Đồng thời, nó cho phép tạo ra các benchmark queries thực tế và phong phú.*

### Data Inventory

| # | Tên tài liệu | Nguồn | Số ký tự | Metadata đã gán |
|---|--------------|-------|----------|-----------------|
| 1 | Savory Pancakes (Bánh Khọt) | vietnamtourism | 1981 | source, extension, category, difficulty, doc_id, chunk_index |
| 2 | Braised Tofu with Quail Eggs | vietnamtourism | 1210 | source, extension, category, difficulty, doc_id, chunk_index |
| 3 | Duck Porridge & Salad (Cháo Gỏi Vịt) | vietnamtourism | 2470 | source, extension, category, difficulty, doc_id, chunk_index |
| 4 | Grilled Snails with Salt & Chili | vietnamtourism | 1014 | source, extension, category, difficulty, doc_id, chunk_index |
| 5 | Orange Fruit Skin Jam (Mứt Vỏ Cam) | vietnamtourism | 1226 | source, extension, category, difficulty, doc_id, chunk_index |

### Metadata Schema
| Trường metadata | Kiểu   | Ví dụ giá trị | Tại sao hữu ích cho retrieval? |
|-----------------|--------|---------------|-------------------------------|
| source | string | "Braised_Tofu" | Tên gốc document — dùng để trace kết quả về file nguồn |
| extension | string | ".md" | Loại file — hỗ trợ filter theo định dạng nếu mix .md/.txt |
| category | string | "main_dish", "seafood", "dessert" | Filter theo loại món — VD: chỉ tìm trong dessert hoặc seafood |
| difficulty | string | "easy", "medium", "hard" | Filter theo độ khó — VD: chỉ tìm món dễ nấu |
| doc_id | string | "Orange_Fruit_Skin_Jam" | ID gốc của document trước khi chunk — dùng để delete_document và group chunks cùng nguồn |
| chunk_index | int | 0, 1, 2... | Vị trí chunk trong document — hỗ trợ debug và tái tạo thứ tự nội dung gốc |

---

## 3. Chunking Strategy — Cá nhân chọn, nhóm so sánh (15 điểm)

### Baseline Analysis

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Strategy | Chunk Count | Avg Length | Preserves Context? |
|-----------|----------|-------------|------------|-------------------|
| `Duck_Porridge.md` | FixedSizeChunker (`fixed_size`) | 6 | 453.33 | Rất kém, cắt ngang từ vựng và câu (Ví dụ: chữ "scallion" bị cắt rời thành "1 bunch Vietnamese" và chunk tiếp theo là "lion, cleaned..."). |
| `Duck_Porridge.md` | SentenceChunker (`by_sentences`) | 10 | 246.10 | Khá hơn, giữ được ranh giới câu trọn vẹn nhưng lại gộp chung lộn xộn các thành phần trong danh sách nguyên liệu. |
| `Duck_Porridge.md` | RecursiveChunker (`recursive`) | 7 | 352.00 | Tốt nhất trong 3 baseline. Bảo toàn được các đoạn văn lớn và danh sách tốt hơn nhờ ưu tiên tách theo dấu xuống dòng `\n` và `\n\n`. |

### Strategy Của Tôi

**Loại:** Custom strategy (CustomRecipeChunker)

**Mô tả cách hoạt động:**
> *Chiến lược này sử dụng Regular Expression (Regex) để phát hiện các thẻ tiêu đề phần cứng (như `Introduce:`, `Ingredients:`, `Process:`, `Finally:`) và các bước nấu ăn (`Step \d+:`). Sau khi nhận diện, thuật toán tách nội dung dọc theo các ranh giới này, sau đó ghép mỗi tiêu đề với đoạn mô tả liền kề nó để tạo thành các chunk độc lập mang trọn vẹn ngữ cảnh.*

**Tại sao tôi chọn strategy này cho domain nhóm?**
> *Dữ liệu công thức nấu ăn của nhóm có cấu trúc phân tầng rập khuôn (Semantic format). Khác với 3 baseline chia mù quáng theo độ dài ký tự hoặc câu chữ, CustomRecipeChunker nhận thức được định dạng tài liệu. Nó vượt trội hơn 3 cách kia vì đảm bảo không bao giờ cắt ngang một danh sách nguyên liệu đang liệt kê dang dở, hoặc cắt đứt một bước nấu ăn làm đôi, từ đó giúp LLM khi RAG luôn nhận được context hoàn chỉnh nhất.*

**Code snippet (nếu custom):**
```python
class CustomRecipeChunker:
    def chunk(self, text: str) -> list[str]:
        pattern = r'(Introduce:|Ingredients:|Process:|Finally:|Step \d+:)'
        parts = re.split(pattern, text)
        chunks = []
        for i in range(1, len(parts)-1, 2):
            header = parts[i].strip()
            content = parts[i+1].strip()
            if content:
                chunks.append(f"{header}\n{content}")
        return chunks
```

### So Sánh: Strategy của tôi vs Baseline

| Tài liệu | Strategy | Chunk Count | Avg Length | Retrieval Quality? |
|-----------|----------|-------------|------------|--------------------|
| `Duck_Porridge.md` | RecursiveChunker (best baseline) | 7 | 352.00 | Khá tốt, nhưng đôi khi vẫn bị gom chung các phần không liên quan (ví dụ: cuối danh sách nguyên liệu bị dính liền vào phần Process) làm giảm độ tập trung ngữ nghĩa. |
| `Duck_Porridge.md` | **CustomRecipeChunker (của tôi)** | 9 | 272.56 | Rất xuất sắc. Tách bạch hoàn toàn Nguyên liệu thành một chunk độc lập, mỗi bước nấu ăn (Step) là một chunk riêng biệt. |

### So Sánh Với Thành Viên Khác

| Thành viên | Strategy | Chunks | Q1 Top-1 | Q2 Top-1 | Q3 Top-1 | Q4 Top-1 | Q5 Top-1 | Top-3 Relevant |
|-----------|----------|--------|----------|----------|----------|----------|----------|----------------|
| Tôi (Vương Hoàng Giang) | CustomRecipeChunker (by header) | 39 | Braised_Tofu:1 (0.7420) ✓ | Grilled_Snails:5 (0.6438) △ | Duck_Porridge:5 (0.7667) ✓ | Orange_Fruit_Skin_Jam:6 (0.5260) ✓ | Savory_Pancakes:1 (0.6275) ✓ | **5/5** |
| Phạm Anh Dũng | SentenceChunker (3 sentences) | 34 | Braised_Tofu:1 (0.7493) ✓ | Grilled_Snails:2 (0.6763) ✓ | Duck_Porridge:4 (–) ✓ | Orange_Fruit_Skin_Jam:5 (0.4988) ✓ | Savory_Pancakes:1 (0.5978) ✓ | **5/5** |
| Dương Quang Đông | RecursiveChunker (300) | 39 | Braised_Tofu:3 (0.7287) ✓ | Grilled_Snails:3 (0.7001) ✓ | Duck_Porridge:5 (0.7640) ✓ | Orange_Fruit_Skin_Jam:5 (0.5260) ✓ | Savory_Pancakes:4 (0.6530) ✓ | **5/5** |
| Nguyễn Lê Trung | FixedSizeChunker (300/50) | 32 | Braised_Tofu:2 (0.7012) | Grilled_Snails:3 (0.7107) ✓ | Duck_Porridge:5 (0.6558) ✓ | Orange_Fruit_Skin_Jam:4 (0.4947) △ | Savory_Pancakes:2 (0.6186) ✓ | **5/5** |

**Strategy nào tốt nhất cho domain này? Tại sao?**
> *Đối với domain công thức nấu ăn, CustomRecipeChunker là chiến lược xuất sắc nhất. Dữ liệu này có cấu trúc định dạng rất rõ ràng (Semantic format). Việc chia chunk dựa trên tiêu đề (Headers/Steps) giúp bảo toàn trọn vẹn một bước hướng dẫn, mang lại độ chính xác cao hơn hẳn so với việc chia cắt mù quáng theo số lượng ký tự.*

---

## 4. My Approach — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi implement các phần chính trong package `src`.

### Chunking Functions

**`SentenceChunker.chunk`** — approach:
> *Tôi sử dụng regex lookbehind `(?<=[.!?])\s+` để tách ranh giới câu mà vẫn bảo toàn được dấu chấm câu ở cuối. Các câu rỗng hoặc toàn khoảng trắng được loại bỏ (edge case), sau đó ghép các câu lại với nhau theo giới hạn `max_sentences_per_chunk`.*

**`RecursiveChunker.chunk` / `_split`** — approach:
> *Thuật toán chia văn bản bằng ký tự phân cách (separator) đầu tiên; gộp các đoạn lại nếu tổng chiều dài chưa vượt `chunk_size`. Nếu một đoạn đơn lẻ vẫn lớn hơn `chunk_size`, nó tiếp tục gọi đệ quy `_split` với danh sách separators còn lại. Base case (trường hợp cơ sở) là khi đoạn văn bản nhỏ hơn `chunk_size` hoặc khi đã hết separator để chia.*

### EmbeddingStore

**`add_documents` + `search`** — approach:
> *Đối với in-memory store, mỗi document chunk được embed và lưu dưới dạng dictionary (gồm id, content, metadata, embedding) vào một list. Hàm `search` nhúng query, sau đó tính tích vô hướng (dot product) giữa query và tất cả các chunk đã lưu, rồi sắp xếp giảm dần để trả về top K.*

**`search_with_filter` + `delete_document`** — approach:
> *Trong `search_with_filter`, danh sách các chunk sẽ được duyệt để lọc ra các chunk khớp với `metadata_filter` TRƯỚC, sau đó mới tính độ tương đồng similarity để tối ưu hiệu suất. `delete_document` hoạt động bằng cách ghi đè list lưu trữ cũ bằng một list mới không chứa các chunk có `doc_id` tương ứng.*

### KnowledgeBaseAgent

**`answer`** — approach:
> *Agent lấy ra top_k chunks liên quan nhất từ EmbeddingStore, sau đó lặp qua và nối chúng lại thành một chuỗi văn bản với tiền tố `[Chunk i]`. Chuỗi ngữ cảnh (context) này được đưa vào một cấu trúc prompt định sẵn cùng với câu hỏi của người dùng để LLM sinh câu trả lời.*

### Test Results

```
# Paste output of: pytest tests/ -v
```

**Số tests pass:** 42 / 42

---

## 5. Similarity Predictions — Cá nhân (5 điểm)

| Pair | Sentence A | Sentence B | Prediction | Actual Score | Correct? |
|------|------------|------------|------------|--------------|----------|
| 1 | Mince the garlic and chili, then fry them in cooking oil until fragrant. | Crush the garlic and chili, put them in a hot oil pan, and stir well to release the aroma. | High | 0.8713 | Yes |
| 2 | Simmer over low heat for 30 minutes so the meat absorbs the spices. | Cook at a low temperature for about half an hour to make the dish flavorful. | High | 0.6006 | Yes |
| 3 | Braised Tofu with Quail Eggs is a delicious dish for the family. | Gold prices surged sharply on the international market today. | Low | 0.0239 | Yes |
| 4 | Add a little sugar to give the dish a mild sweet flavor. | Absolutely do not add sugar to this dish because it will ruin the taste. | Low | 0.6937 | No |
| 5 | Clean the duck carefully with salt and ginger to remove the bad odor. | Wash the snails with chili water so they release all the mud and dirt. | Low | 0.3588 | Yes |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn nghĩa?**
> *Cặp câu số 4 gây bất ngờ nhất với điểm số khá cao (0.6937). Mặc dù hai câu có ý nghĩa hoàn toàn trái ngược nhau (thêm đường vs tuyệt đối không thêm đường), điểm tương đồng trả về vẫn cao. Điều này chứng tỏ các mô hình embeddings thường biểu diễn nghĩa bằng cách gom nhóm các từ vựng xuất hiện chung bối cảnh (như "sugar", "dish", "flavor"), nhưng lại xử lý khá kém việc nhận diện các từ mang ý nghĩa phủ định ("not", "absolutely").*

---

## 6. Results — Cá nhân (10 điểm)

Chạy 5 benchmark queries của nhóm trên implementation cá nhân của bạn trong package `src`. **5 queries phải trùng với các thành viên cùng nhóm.**

### Benchmark Queries & Gold Answers (nhóm thống nhất)

| # | Query | Gold Answer |
|---|-------|-------------|
| 1 | What ingredients are needed for braised tofu with quail eggs? | 100-200g fried tofu slices, 15-20 quail eggs, spring onion, shallot, salt, fish sauce, sugar, pepper, soy sauce, and Maggi's seasoning powder. |
| 2 | How do you make the dipping sauce for grilled snails? | Mix salt, pepper, lemon juice, and sugar together. Serve with Vietnamese mint herb. |
| 3 | What is the process for making duck porridge? | Boil duck with ginger and grilled onion. Roast sticky rice separately, then cook in broth until soft. Season and top with fried purple onion and pepper. |
| 4 | Which dish is a dessert and how is it stored? | Orange Fruit Skin Jam (Mut Vo Cam). After cooking, wait to cool, then store in a jar and use day by day. |
| 5 | Which dishes require shrimp as an ingredient? | Vietnamese Mini Savory Pancakes (Banh Khot) require fresh shrimps (10 pieces, boiled and cut in half) and dried shrimp (100g, ground well). |

### Kết Quả Của Tôi

| # | Query | Top-1 Retrieved Chunk (tóm tắt) | Score | Relevant? | Agent Answer (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | What ingredients are needed for braised tofu... | Ingredients: 100 – 200g fried tofu slices... | 0.7420 | Yes | 100-200g fried tofu slices, 15-20 quail eggs... |
| 2 | How do you make the dipping sauce for grilled snails? | Step 4: Bring all snails to grill with fired coal... | 0.6438 | No | Bring all snails to grill with fired coal... (Trả lời sai) |
| 3 | What is the process for making duck porridge? | Step 4: Making Duck Porridge: When duck is boiled... | 0.7667 | Yes | When duck is boiled, take it out, wait to cold... |
| 4 | Which dish is a dessert and how is it stored? | Finally: Your dessert is ready bring to serve. Wait... | 0.5260 | Partial | Wait to get cold, store into jar and use day by day. |
| 5 | Which dishes require shrimp as an ingredient? | Ingredients: 1 bowl rice flour 2 bowls coconut milk... | 0.6275 | Yes | 10 fresh shrimps, 100gr dried shrimp... |

**Bao nhiêu queries trả về chunk relevant trong top-3?** 4 / 5

---

## 7. What I Learned (5 điểm — Demo)

**Điều hay nhất tôi học được từ thành viên khác trong nhóm:**
> *Tôi học được rằng việc lựa chọn chiến lược Chunking ảnh hưởng cực kỳ lớn đến kết quả. Một chiến lược Semantic Chunking giúp bảo toàn danh sách nguyên liệu và các bước nấu ăn tốt hơn hẳn so với việc chia cắt mù quáng theo độ dài (FixedSize).*

**Điều hay nhất tôi học được từ nhóm khác (qua demo):**
> *Thông qua demo của các nhóm khác, tôi nhận ra tầm quan trọng của Embedding Model và sự nguy hiểm của "Context Loss". Ở câu hỏi số 4 và 5, hệ thống tìm đúng chunk nguyên liệu/bảo quản, nhưng lại không có tên món ăn do chunk đó nằm ở cuối file, tách biệt hoàn toàn với tên món ăn ở đầu file.*

**Nếu làm lại, tôi sẽ thay đổi gì trong data strategy?**
> *Tôi sẽ cải tiến chiến lược Chunking bằng cách thêm (inject) Tên món ăn (hoặc các metadata quan trọng) vào đầu mỗi chunk trước khi đưa đi embed. Ví dụ, thay vì lưu `Step 1:...`, tôi sẽ lưu `[Orange Fruit Skin Jam] Step 1:...`. Điều này sẽ giúp mô hình luôn biết đoạn text đó thuộc về món ăn nào, khắc phục hoàn toàn failure case ở câu hỏi 4 và 5.*

---

## Tự Đánh Giá

| Tiêu chí | Loại | Điểm tự đánh giá |
|----------|------|-------------------|
| Warm-up | Cá nhân | / 5 |
| Document selection | Nhóm | / 10 |
| Chunking strategy | Nhóm | / 15 |
| My approach | Cá nhân | / 10 |
| Similarity predictions | Cá nhân | / 5 |
| Results | Cá nhân | / 10 |
| Core implementation (tests) | Cá nhân | / 30 |
| Demo | Nhóm | / 5 |
| **Tổng** | | **/ 100** |
