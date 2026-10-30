fn main() {
    let candidate = heap_queue_largest;
    assert_eq!(candidate(vec![25, 35, 22, 85, 14, 65, 75, 22, 58], 3), vec![85, 75, 65]);
    assert_eq!(candidate(vec![25, 35, 22, 85, 14, 65, 75, 22, 58], 2), vec![85, 75]);
    assert_eq!(candidate(vec![25, 35, 22, 85, 14, 65, 75, 22, 58], 5), vec![85, 75, 65, 58, 35]);
}
