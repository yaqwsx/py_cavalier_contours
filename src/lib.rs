pub use cavalier_contours_ffi::*;

use cavalier_contours::core::math::Vector2;
use cavalier_contours::polyline::{
    FindIntersectsOptions, PlineBasicIntersect, PlineCreation, PlineOverlappingIntersect,
    PlineSource, Polyline,
};

/// Catch panics from FFI functions and return -1 on panic.
macro_rules! ffi_catch_unwind {
    ($body:expr) => {
        match std::panic::catch_unwind(std::panic::AssertUnwindSafe(move || $body)) {
            Ok(r) => r,
            Err(_) => -1,
        }
    };
}

const CAVC_ERROR_NULL_INPUT: i32 = 1;
const CAVC_ERROR_INVALID_INPUT: i32 = 2;
const CAVC_ERROR_NULL_OUTPUT: i32 = 3;

// ============================================================================
// Orientation
// ============================================================================

/// Get the orientation of a polyline.
///
/// Writes to `orientation`: 0 = Open, 1 = Clockwise, 2 = CounterClockwise.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline` is null.
/// * 2 = `orientation` is null.
///
/// # Safety
///
/// `pline` must be null or point to a valid, live [`cavc_pline`]. `orientation` must be null or
/// point to writable memory for a `u32`.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_orientation(
    pline: *const cavc_pline,
    orientation: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if orientation.is_null() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        let p = unsafe { &(*pline).0 };
        let o = p.orientation();
        unsafe {
            *orientation = match o {
                cavalier_contours::polyline::PlineOrientation::Open => 0,
                cavalier_contours::polyline::PlineOrientation::Clockwise => 1,
                cavalier_contours::polyline::PlineOrientation::CounterClockwise => 2,
            };
        }
        0
    })
}

// ============================================================================
// Closest point
// ============================================================================

/// Find the closest point on a polyline to a given point.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline` is null.
/// * 2 = polyline is empty (no segments).
/// * 3 = one or more output pointers are null.
///
/// # Safety
///
/// `pline` must be null or point to a valid, live [`cavc_pline`]. Every output pointer must be null
/// or point to writable memory of its corresponding type.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_closest_point(
    pline: *const cavc_pline,
    x: f64,
    y: f64,
    pos_equal_eps: f64,
    seg_start_index: *mut u32,
    closest_x: *mut f64,
    closest_y: *mut f64,
    distance: *mut f64,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if seg_start_index.is_null()
            || closest_x.is_null()
            || closest_y.is_null()
            || distance.is_null()
        {
            return CAVC_ERROR_NULL_OUTPUT;
        }
        let p = unsafe { &(*pline).0 };
        if p.segment_count() == 0 {
            return CAVC_ERROR_INVALID_INPUT;
        }
        match p.closest_point(Vector2::new(x, y), pos_equal_eps) {
            Some(result) => {
                unsafe {
                    *seg_start_index = result.seg_start_index as u32;
                    *closest_x = result.seg_point.x;
                    *closest_y = result.seg_point.y;
                    *distance = result.distance;
                }
                0
            }
            None => CAVC_ERROR_INVALID_INPUT,
        }
    })
}

// ============================================================================
// Find point at path length
// ============================================================================

/// Find the point at a given path length along a polyline.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline` is null.
/// * 2 = polyline is empty or target length exceeds total path length.
/// * 3 = one or more output pointers are null.
///
/// # Safety
///
/// `pline` must be null or point to a valid, live [`cavc_pline`]. Every output pointer must be null
/// or point to writable memory of its corresponding type.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_find_point_at_path_length(
    pline: *const cavc_pline,
    target_path_length: f64,
    seg_index: *mut u32,
    point_x: *mut f64,
    point_y: *mut f64,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if seg_index.is_null() || point_x.is_null() || point_y.is_null() {
            return CAVC_ERROR_NULL_OUTPUT;
        }
        let p = unsafe { &(*pline).0 };
        match p.find_point_at_path_length(target_path_length) {
            Ok((idx, point)) => {
                unsafe {
                    *seg_index = idx as u32;
                    *point_x = point.x;
                    *point_y = point.y;
                }
                0
            }
            Err(_) => CAVC_ERROR_INVALID_INPUT,
        }
    })
}

// ============================================================================
// Arcs to approximate lines
// ============================================================================

/// Convert all arc segments to approximate line segments.
///
/// Returns a new polyline via `result`.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline` is null.
/// * 2 = `result` is null.
///
/// # Safety
///
/// `pline` must be null or point to a valid, live [`cavc_pline`]. `result` must be null or point to
/// writable memory for a polyline pointer. Before computation, a valid `result` is initialized to
/// null, and ownership of any successful non-null result is transferred to the caller.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_arcs_to_approx_lines(
    pline: *const cavc_pline,
    error_distance: f64,
    result: *mut *mut cavc_pline,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if result.is_null() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        unsafe {
            result.write(std::ptr::null_mut());
        }
        let p = unsafe { &(*pline).0 };
        let linearized = match p.arcs_to_approx_lines(error_distance) {
            Some(pl) => pl,
            None => Polyline::create_from(p),
        };
        let boxed = Box::new(cavc_pline(linearized));
        unsafe {
            *result = Box::into_raw(boxed);
        }
        0
    })
}

// ============================================================================
// Rotate start
// ============================================================================

/// Rotate the start of a closed polyline to a new index and split point.
///
/// Modifies in place.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline` is null.
/// * 2 = operation failed (open polyline or invalid index).
///
/// # Safety
///
/// `pline` must be null or point to a valid, live, uniquely borrowed [`cavc_pline`].
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_rotate_start(
    pline: *mut cavc_pline,
    start_index: u32,
    point_x: f64,
    point_y: f64,
    pos_equal_eps: f64,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        let p = unsafe { &mut (*pline).0 };
        let point = Vector2::new(point_x, point_y);
        match PlineSource::rotate_start(p, start_index as usize, point, pos_equal_eps) {
            Some(rotated) => {
                *p = rotated;
                0
            }
            None => CAVC_ERROR_INVALID_INPUT,
        }
    })
}

// ============================================================================
// Find intersects between two polylines
// ============================================================================

/// Opaque type holding intersection results between two polylines.
#[allow(non_camel_case_types)]
pub struct cavc_intersects_result {
    pub basic: Vec<PlineBasicIntersect<f64>>,
    pub overlapping: Vec<PlineOverlappingIntersect<f64>>,
}

/// Represents a basic (single-point) intersection.
#[repr(C)]
pub struct cavc_basic_intersect {
    pub start_index1: u32,
    pub start_index2: u32,
    pub point_x: f64,
    pub point_y: f64,
}

/// Represents an overlapping intersection (two points).
#[repr(C)]
pub struct cavc_overlapping_intersect {
    pub start_index1: u32,
    pub start_index2: u32,
    pub point1_x: f64,
    pub point1_y: f64,
    pub point2_x: f64,
    pub point2_y: f64,
}

/// Find all intersections between two polylines.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `pline1` or `pline2` is null.
/// * 2 = `result` is null.
///
/// # Safety
///
/// Both polyline pointers must be null or point to valid, live [`cavc_pline`] values. `result` must
/// be null or point to writable memory for an intersection-result pointer. Before computation, a
/// valid `result` is initialized to null, and ownership of any successful result is transferred to
/// the caller.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_pline_find_intersects(
    pline1: *const cavc_pline,
    pline2: *const cavc_pline,
    pos_equal_eps: f64,
    result: *mut *mut cavc_intersects_result,
) -> i32 {
    ffi_catch_unwind!({
        if pline1.is_null() || pline2.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if result.is_null() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        unsafe {
            result.write(std::ptr::null_mut());
        }
        let p1 = unsafe { &(*pline1).0 };
        let p2 = unsafe { &(*pline2).0 };
        let opts = FindIntersectsOptions {
            pline1_aabb_index: None,
            pos_equal_eps,
        };
        let collection = p1.find_intersects_opt(p2, &opts);
        let boxed = Box::new(cavc_intersects_result {
            basic: collection.basic_intersects,
            overlapping: collection.overlapping_intersects,
        });
        unsafe {
            *result = Box::into_raw(boxed);
        }
        0
    })
}

/// Get the count of basic intersections.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `result` is null.
/// * 2 = `count` is null.
///
/// # Safety
///
/// `result` must be null or point to a valid, live [`cavc_intersects_result`]. `count` must be null
/// or point to writable memory for a `u32`.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_intersects_result_get_basic_count(
    result: *const cavc_intersects_result,
    count: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if count.is_null() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        unsafe {
            *count = (*result).basic.len() as u32;
        }
        0
    })
}

/// Get a basic intersection at the given index.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `result` is null.
/// * 2 = `index` is out of range.
/// * 3 = `intr` is null.
///
/// # Safety
///
/// `result` must be null or point to a valid, live [`cavc_intersects_result`]. `intr` must be null
/// or point to writable memory for a [`cavc_basic_intersect`].
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_intersects_result_get_basic(
    result: *const cavc_intersects_result,
    index: u32,
    intr: *mut cavc_basic_intersect,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if intr.is_null() {
            return CAVC_ERROR_NULL_OUTPUT;
        }
        let r = unsafe { &*result };
        let idx = index as usize;
        if idx >= r.basic.len() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        let b = &r.basic[idx];
        unsafe {
            *intr = cavc_basic_intersect {
                start_index1: b.start_index1 as u32,
                start_index2: b.start_index2 as u32,
                point_x: b.point.x,
                point_y: b.point.y,
            };
        }
        0
    })
}

/// Get the count of overlapping intersections.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `result` is null.
/// * 2 = `count` is null.
///
/// # Safety
///
/// `result` must be null or point to a valid, live [`cavc_intersects_result`]. `count` must be null
/// or point to writable memory for a `u32`.
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_intersects_result_get_overlapping_count(
    result: *const cavc_intersects_result,
    count: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if count.is_null() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        unsafe {
            *count = (*result).overlapping.len() as u32;
        }
        0
    })
}

/// Get an overlapping intersection at the given index.
///
/// ## Error Codes
/// * -1 = unexpected internal panic.
/// * 1 = `result` is null.
/// * 2 = `index` is out of range.
/// * 3 = `intr` is null.
///
/// # Safety
///
/// `result` must be null or point to a valid, live [`cavc_intersects_result`]. `intr` must be null
/// or point to writable memory for a [`cavc_overlapping_intersect`].
#[unsafe(no_mangle)]
#[must_use]
pub unsafe extern "C" fn cavc_intersects_result_get_overlapping(
    result: *const cavc_intersects_result,
    index: u32,
    intr: *mut cavc_overlapping_intersect,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return CAVC_ERROR_NULL_INPUT;
        }
        if intr.is_null() {
            return CAVC_ERROR_NULL_OUTPUT;
        }
        let r = unsafe { &*result };
        let idx = index as usize;
        if idx >= r.overlapping.len() {
            return CAVC_ERROR_INVALID_INPUT;
        }
        let o = &r.overlapping[idx];
        unsafe {
            *intr = cavc_overlapping_intersect {
                start_index1: o.start_index1 as u32,
                start_index2: o.start_index2 as u32,
                point1_x: o.point1.x,
                point1_y: o.point1.y,
                point2_x: o.point2.x,
                point2_y: o.point2.y,
            };
        }
        0
    })
}

/// Free an intersection result.
///
/// # Safety
///
/// `result` must be null or a pointer returned by [`cavc_pline_find_intersects`] that has not
/// already been freed.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_f(result: *mut cavc_intersects_result) {
    if !result.is_null() {
        unsafe {
            drop(Box::from_raw(result));
        }
    }
}

#[cfg(test)]
mod tests {
    use std::ptr::{null, null_mut};

    use cavalier_contours::polyline::PlineSourceMut;

    use super::*;

    fn pline_with_segment() -> *mut cavc_pline {
        pline_from_points(&[(0.0, 0.0), (1.0, 0.0)], false)
    }

    fn pline_from_points(points: &[(f64, f64)], closed: bool) -> *mut cavc_pline {
        let mut pline = Polyline::new();
        pline.set_is_closed(closed);
        for &(x, y) in points {
            pline.add(x, y, 0.0);
        }
        Box::into_raw(Box::new(cavc_pline(pline)))
    }

    #[test]
    fn custom_ffi_rejects_null_output_pointers() {
        let pline = pline_with_segment();
        let empty_result = Box::into_raw(Box::new(cavc_intersects_result {
            basic: Vec::new(),
            overlapping: Vec::new(),
        }));

        unsafe {
            assert_eq!(cavc_pline_orientation(pline, null_mut()), 2);
            assert_eq!(
                cavc_pline_closest_point(
                    pline,
                    0.5,
                    1.0,
                    1e-5,
                    null_mut(),
                    null_mut(),
                    null_mut(),
                    null_mut(),
                ),
                3
            );
            assert_eq!(
                cavc_pline_find_point_at_path_length(
                    pline,
                    0.5,
                    null_mut(),
                    null_mut(),
                    null_mut(),
                ),
                3
            );
            assert_eq!(cavc_pline_arcs_to_approx_lines(pline, 0.01, null_mut()), 2);
            assert_eq!(
                cavc_pline_find_intersects(pline, pline, 1e-5, null_mut()),
                2
            );
            assert_eq!(
                cavc_intersects_result_get_basic_count(empty_result, null_mut()),
                2
            );
            assert_eq!(
                cavc_intersects_result_get_basic(empty_result, 0, null_mut()),
                3
            );
            assert_eq!(
                cavc_intersects_result_get_overlapping_count(empty_result, null_mut()),
                2
            );
            assert_eq!(
                cavc_intersects_result_get_overlapping(empty_result, 0, null_mut()),
                3
            );

            cavc_pline_f(pline);
            cavc_intersects_result_f(empty_result);
        }
    }

    #[test]
    fn custom_ffi_preserves_null_input_precedence() {
        unsafe {
            assert_eq!(cavc_pline_orientation(null(), null_mut()), 1);
            assert_eq!(
                cavc_pline_find_intersects(null(), null(), 1e-5, null_mut()),
                1
            );
            assert_eq!(
                cavc_intersects_result_get_basic_count(null(), null_mut()),
                1
            );
        }
    }

    #[test]
    fn custom_ffi_returns_owned_handles() {
        let pline = pline_with_segment();
        let mut linearized = null_mut();
        let mut intersects = null_mut();

        unsafe {
            assert_eq!(
                cavc_pline_arcs_to_approx_lines(pline, 0.01, &mut linearized),
                0
            );
            assert!(!linearized.is_null());

            assert_eq!(
                cavc_pline_find_intersects(pline, linearized, 1e-5, &mut intersects),
                0
            );
            assert!(!intersects.is_null());

            cavc_intersects_result_f(intersects);
            cavc_pline_f(linearized);
            cavc_pline_f(pline);
        }
    }

    #[test]
    fn custom_ffi_evaluates_orientation_and_point_queries() {
        let pline = pline_with_segment();
        let mut orientation = u32::MAX;
        let mut segment_index = u32::MAX;
        let mut x = f64::NAN;
        let mut y = f64::NAN;
        let mut distance = f64::NAN;

        unsafe {
            assert_eq!(cavc_pline_orientation(pline, &mut orientation), 0);
            assert_eq!(orientation, 0);

            assert_eq!(
                cavc_pline_closest_point(
                    pline,
                    0.5,
                    1.0,
                    1e-5,
                    &mut segment_index,
                    &mut x,
                    &mut y,
                    &mut distance,
                ),
                0
            );
            assert_eq!(segment_index, 0);
            assert!((x - 0.5).abs() < 1e-12);
            assert!(y.abs() < 1e-12);
            assert!((distance - 1.0).abs() < 1e-12);

            assert_eq!(
                cavc_pline_find_point_at_path_length(
                    pline,
                    0.25,
                    &mut segment_index,
                    &mut x,
                    &mut y,
                ),
                0
            );
            assert_eq!(segment_index, 0);
            assert!((x - 0.25).abs() < 1e-12);
            assert!(y.abs() < 1e-12);

            assert_eq!(
                cavc_pline_find_point_at_path_length(
                    pline,
                    2.0,
                    &mut segment_index,
                    &mut x,
                    &mut y,
                ),
                2
            );
            cavc_pline_f(pline);
        }
    }

    #[test]
    fn custom_ffi_rotates_closed_polyline_and_rejects_open_polyline() {
        let square = pline_from_points(&[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], true);
        let open = pline_with_segment();

        unsafe {
            assert_eq!(cavc_pline_rotate_start(square, 2, 1.0, 1.0, 1e-5), 0);
            let rotated = &(*square).0;
            assert!((rotated[0].x - 1.0).abs() < 1e-12);
            assert!((rotated[0].y - 1.0).abs() < 1e-12);

            assert_eq!(cavc_pline_rotate_start(open, 0, 0.0, 0.0, 1e-5), 2);
            cavc_pline_f(square);
            cavc_pline_f(open);
        }
    }

    #[test]
    fn custom_ffi_extracts_basic_and_overlapping_intersections() {
        let horizontal = pline_from_points(&[(0.0, 0.0), (3.0, 0.0)], false);
        let vertical = pline_from_points(&[(1.0, -1.0), (1.0, 1.0)], false);
        let overlapping = pline_from_points(&[(1.0, 0.0), (2.0, 0.0)], false);
        let mut basic_result = null_mut();
        let mut overlap_result = null_mut();

        unsafe {
            assert_eq!(
                cavc_pline_find_intersects(horizontal, vertical, 1e-5, &mut basic_result,),
                0
            );
            let mut count = 0;
            assert_eq!(
                cavc_intersects_result_get_basic_count(basic_result, &mut count),
                0
            );
            assert_eq!(count, 1);
            let mut basic = cavc_basic_intersect {
                start_index1: u32::MAX,
                start_index2: u32::MAX,
                point_x: f64::NAN,
                point_y: f64::NAN,
            };
            assert_eq!(
                cavc_intersects_result_get_basic(basic_result, 0, &mut basic),
                0
            );
            assert_eq!(basic.start_index1, 0);
            assert_eq!(basic.start_index2, 0);
            assert!((basic.point_x - 1.0).abs() < 1e-12);
            assert!(basic.point_y.abs() < 1e-12);
            assert_eq!(
                cavc_intersects_result_get_basic(basic_result, 1, &mut basic),
                2
            );

            assert_eq!(
                cavc_pline_find_intersects(horizontal, overlapping, 1e-5, &mut overlap_result,),
                0
            );
            assert_eq!(
                cavc_intersects_result_get_overlapping_count(overlap_result, &mut count),
                0
            );
            assert_eq!(count, 1);
            let mut overlap = cavc_overlapping_intersect {
                start_index1: u32::MAX,
                start_index2: u32::MAX,
                point1_x: f64::NAN,
                point1_y: f64::NAN,
                point2_x: f64::NAN,
                point2_y: f64::NAN,
            };
            assert_eq!(
                cavc_intersects_result_get_overlapping(overlap_result, 0, &mut overlap),
                0
            );
            assert_eq!(overlap.start_index1, 0);
            assert_eq!(overlap.start_index2, 0);
            assert!((overlap.point1_x - 1.0).abs() < 1e-12);
            assert!((overlap.point2_x - 2.0).abs() < 1e-12);
            assert!(overlap.point1_y.abs() < 1e-12);
            assert!(overlap.point2_y.abs() < 1e-12);
            assert_eq!(
                cavc_intersects_result_get_overlapping(overlap_result, 1, &mut overlap),
                2
            );

            cavc_intersects_result_f(basic_result);
            cavc_intersects_result_f(overlap_result);
            cavc_intersects_result_f(null_mut());
            cavc_pline_f(horizontal);
            cavc_pline_f(vertical);
            cavc_pline_f(overlapping);
        }
    }
}
