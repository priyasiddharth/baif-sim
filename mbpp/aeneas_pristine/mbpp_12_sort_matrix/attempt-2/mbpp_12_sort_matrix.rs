/// Write a function to sort a given matrix in ascending order according to the sum of its rows.
fn sort_matrix(M: Vec<Vec<isize>>) -> Vec<Vec<isize>> {
    let n = M.len();
    // Row sums by index loops (no Iterator::sum).
    let mut sums: Vec<isize> = Vec::new();
    let mut i = 0;
    while i < n {
        let mut s = 0;
        let mut j = 0;
        while j < M[i].len() {
            s += M[i][j];
            j += 1;
        }
        sums.push(s);
        i += 1;
    }
    // Stable selection: repeatedly take the unused row with the smallest sum
    // and copy it into the output (no sort/swap/clone).
    let mut used: Vec<bool> = Vec::new();
    let mut k = 0;
    while k < n {
        used.push(false);
        k += 1;
    }
    let mut out: Vec<Vec<isize>> = Vec::new();
    let mut taken = 0;
    while taken < n {
        let mut best = n;
        let mut r = 0;
        while r < n {
            if !used[r] && (best == n || sums[r] < sums[best]) {
                best = r;
            }
            r += 1;
        }
        used[best] = true;
        let mut row: Vec<isize> = Vec::new();
        let mut c = 0;
        while c < M[best].len() {
            row.push(M[best][c]);
            c += 1;
        }
        out.push(row);
        taken += 1;
    }
    out
}
