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

// ============================================================================
// Orientation
// ============================================================================

/// Get the orientation of a polyline.
///
/// Writes to `orientation`: 0 = Open, 1 = Clockwise, 2 = CounterClockwise.
///
/// ## Error Codes
/// * 1 = `pline` is null.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_pline_orientation(
    pline: *const cavc_pline,
    orientation: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return 1;
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
/// * 1 = `pline` is null.
/// * 2 = polyline is empty (no segments).
#[unsafe(no_mangle)]
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
            return 1;
        }
        let p = unsafe { &(*pline).0 };
        if p.segment_count() == 0 {
            return 2;
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
            None => 2,
        }
    })
}

// ============================================================================
// Find point at path length
// ============================================================================

/// Find the point at a given path length along a polyline.
///
/// ## Error Codes
/// * 1 = `pline` is null.
/// * 2 = polyline is empty or target length exceeds total path length.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_pline_find_point_at_path_length(
    pline: *const cavc_pline,
    target_path_length: f64,
    seg_index: *mut u32,
    point_x: *mut f64,
    point_y: *mut f64,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return 1;
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
            Err(_) => 2,
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
/// * 1 = `pline` is null.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_pline_arcs_to_approx_lines(
    pline: *const cavc_pline,
    error_distance: f64,
    result: *mut *mut cavc_pline,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return 1;
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
/// * 1 = `pline` is null.
/// * 2 = operation failed (open polyline or invalid index).
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_pline_rotate_start(
    pline: *mut cavc_pline,
    start_index: u32,
    point_x: f64,
    point_y: f64,
    pos_equal_eps: f64,
) -> i32 {
    ffi_catch_unwind!({
        if pline.is_null() {
            return 1;
        }
        let p = unsafe { &mut (*pline).0 };
        let point = Vector2::new(point_x, point_y);
        match PlineSource::rotate_start(p, start_index as usize, point, pos_equal_eps) {
            Some(rotated) => {
                *p = rotated;
                0
            }
            None => 2,
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
/// * 1 = `pline1` or `pline2` is null.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_pline_find_intersects(
    pline1: *const cavc_pline,
    pline2: *const cavc_pline,
    pos_equal_eps: f64,
    result: *mut *mut cavc_intersects_result,
) -> i32 {
    ffi_catch_unwind!({
        if pline1.is_null() || pline2.is_null() {
            return 1;
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
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_get_basic_count(
    result: *const cavc_intersects_result,
    count: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return 1;
        }
        unsafe {
            *count = (*result).basic.len() as u32;
        }
        0
    })
}

/// Get a basic intersection at the given index.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_get_basic(
    result: *const cavc_intersects_result,
    index: u32,
    intr: *mut cavc_basic_intersect,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return 1;
        }
        let r = unsafe { &*result };
        let idx = index as usize;
        if idx >= r.basic.len() {
            return 2;
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
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_get_overlapping_count(
    result: *const cavc_intersects_result,
    count: *mut u32,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return 1;
        }
        unsafe {
            *count = (*result).overlapping.len() as u32;
        }
        0
    })
}

/// Get an overlapping intersection at the given index.
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_get_overlapping(
    result: *const cavc_intersects_result,
    index: u32,
    intr: *mut cavc_overlapping_intersect,
) -> i32 {
    ffi_catch_unwind!({
        if result.is_null() {
            return 1;
        }
        let r = unsafe { &*result };
        let idx = index as usize;
        if idx >= r.overlapping.len() {
            return 2;
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
#[unsafe(no_mangle)]
pub unsafe extern "C" fn cavc_intersects_result_f(result: *mut cavc_intersects_result) {
    if !result.is_null() {
        unsafe {
            drop(Box::from_raw(result));
        }
    }
}
